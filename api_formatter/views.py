from django.http import Http404
from django_elasticsearch_dsl_drf.pagination import LimitOffsetPagination
from elasticsearch_dsl import A, Q
from rac_es.documents import (Agent, BaseDescriptionComponent, Collection,
                              Object, Term)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .pagination import CollapseLimitOffsetPagination
from .serializers import (AgentListSerializer, AgentSerializer,
                          AncestorsSerializer, CollectionHitSerializer,
                          CollectionListSerializer, CollectionSerializer,
                          FacetSerializer, ObjectListSerializer,
                          ObjectSerializer, ReferenceSerializer,
                          TermListSerializer, TermSerializer)
from .view_helpers import (FILTER_BACKENDS, NUMBER_LOOKUPS, SEARCH_BACKENDS,
                           STRING_LOOKUPS, ChildrenPaginator, SearchMixin,
                           text_from_notes)


class AncestorMixin(object):
    """Provides an ancestors detail route.

    Returns a nested dictionary representation of the complete ancestor tree for
    a collection or object.
    """

    @action(detail=True)
    def ancestors(self, request, pk=None):
        base_query = self.search.query()
        obj = self.resolve_object(self.document, pk, source_fields=["ancestors"])
        ancestors = list(getattr(obj, "ancestors", []))
        if ancestors:
            resource = self.resolve_object(Collection, obj.ancestors[-1].identifier, source_fields=["ancestors"])
            if getattr(resource, "ancestors", None):
                ancestors += list(resource.ancestors)
        for a in ancestors:
            a.description = self.get_description(Collection, a.identifier)
            if self.request.GET.get("query"):
                a.hit_count = self.get_hit_count(a.identifier, base_query)
        serializer = AncestorsSerializer(ancestors)
        return Response(serializer.data)


class DocumentViewSet(SearchMixin, ReadOnlyModelViewSet):
    filter_backends = FILTER_BACKENDS
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.action == "list":
            try:
                return self.list_serializer
            except AttributeError:
                return self.serializer
        return self.serializer

    def get_queryset(self):
        """Returns only certain fields to improve performance of list views."""
        query = self.search.query()
        if self.action == "list":
            query = query.source(self.list_fields)
        return query.source(exclude=["ancestors"])

    def get_object(self):
        """Returns a specific object."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        queryset = self.get_queryset().filter(
            "match_phrase", **{"_id": self.kwargs[lookup_url_kwarg]}
        )
        hits = queryset.execute().hits
        count = len(hits)
        if count != 1:
            message = (
                "No object matches the given query."
                if count == 0
                else "Multiple results matches the given query. Expected a single result."
            )
            raise Http404(message)
        else:
            return hits[0]

    def resolve_object(self, object_type, identifier, source_fields=None):
        """Returns an object based on object type and identifier.

        Provides `source_fields` argument to allow for performant retrieval of
        specific fields.

        Returns an empty dictionary if object is not found.
        """
        queryset = object_type.search(using=self.client).query().filter(
            "match_phrase", **{"_id": identifier}
        )
        hits = queryset.source(source_fields).execute().hits if source_fields else queryset.execute().hits
        count = len(hits)
        if count != 1:
            return {}
        else:
            return hits[0]

    def get_hit_count(self, identifier, base_query):
        """Gets the number of hits that are childrend of a specific component."""
        q = Q("nested", path="ancestors", query=Q("match", ancestors__identifier=identifier))
        queryset = base_query.query(q)
        query_dict = self.filter_queryset(queryset).to_dict()
        query_dict["query"]["bool"].pop("filter", None)
        self.search.query = query_dict["query"]
        return self.search.query().count()

    @property
    def list_fields(self):
        return list(set(list(self.filter_fields) + list(self.ordering_fields) + list(self.search_fields) + ["type", "dates"]))


class AgentViewSet(DocumentViewSet):
    """Returns data about agents, including people, organizations and families."""

    document = Agent
    list_serializer = AgentListSerializer
    serializer = AgentSerializer
    relations = ("collections", "objects")

    filter_fields = {
        "title": {"field": "title.keyword", "lookups": STRING_LOOKUPS, },
        "agent_type": {"field": "agent_type", "lookups": STRING_LOOKUPS, },
        "start_date": {"field": "dates.begin", "lookups": NUMBER_LOOKUPS, },
        "end_date": {"field": "dates.end", "lookups": NUMBER_LOOKUPS, },
    }

    search_fields = ("title", "description")
    search_nested_fields = {
        "notes": {"path": "notes", "fields": ["subnotes.content"]},
    }

    ordering_fields = {
        "title": "title.keyword",
        "type": "type.keyword",
        "start_date": "dates.begin",
        "end_date": "dates.end",
    }


class CollectionViewSet(DocumentViewSet, AncestorMixin):
    """Returns data about collections, or intellectually significant groups of archival records."""

    document = Collection
    list_serializer = CollectionListSerializer
    serializer = CollectionSerializer
    filter_backends = SEARCH_BACKENDS

    filter_fields = {
        "category": {"field": "category", "lookups": STRING_LOOKUPS},
        "level": {"field": "level.keyword", "lookups": STRING_LOOKUPS, },
        "end_date": {"field": "dates.end", "lookups": NUMBER_LOOKUPS},
        "genre": {"field": "formats", "lookups": STRING_LOOKUPS},
        "online": "online",
        "start_date": {"field": "dates.begin", "lookups": NUMBER_LOOKUPS},
    }
    nested_filter_fields = {
        "subject": {
            "field": "terms.title.keyword",
            "path": "terms",
        },
        "creator": {
            "field": "creators.title.keyword",
            "path": "creators"
        }
    }

    search_fields = ("title",)
    search_nested_fields = {
        "notes": {"path": "notes", "fields": ["subnotes.content"]},
    }

    ordering_fields = {
        "title": "title.keyword",
        "level": "level.keyword",
        "start_date": "dates.begin",
        "end_date": "dates.end",
    }

    def get_description(self, object_type, identifier):
        """Gets text from all published Abstracts or Scope and Contents notes."""
        resolved = self.resolve_object(object_type, identifier, source_fields=["notes"])
        notes = getattr(resolved, "notes", [])
        return text_from_notes(notes, "abstract") if text_from_notes(notes, "abstract") else text_from_notes(notes, "scopecontent")

    def prepare_children(self, children, group):
        """Appends additional data to each child object.

        Adds `group` information from the parent collection and a `description`
        field (either the abstract or scope and contents) from child objects.

        If a query parameter exists, fetches the hit count. Removes default
        filtering on `type` field."""
        base_query = self.search.query()
        for c in children:
            c.group = group  # append group from parent collection
            obj_type = Object if c.type == "object" else Collection
            c.description = self.get_description(obj_type, c.identifier)
            if self.request.GET.get("query"):
                c.hit_count = self.get_hit_count(c.identifier, base_query)
        return children

    @action(detail=True)
    def children(self, request, pk=None):
        """Provides a detail endpoint for a collection's children."""
        obj = self.resolve_object(Collection, pk, source_fields=["children", "group"])
        paginator = ChildrenPaginator()
        page = paginator.paginate_queryset(obj.children, request)
        if page is not None:
            page = self.prepare_children(page, obj.group)
            serializer = ReferenceSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        children = self.prepare_children(obj.children, obj.group)
        serializer = ReferenceSerializer(children, many=True)
        return paginator.get_paginated_response(serializer.data)

    def get_object(self):
        """Fetches the hit count for each child components of a collection.

        If a query parameter exists, searches for hits which include the
        identifier of each child in the document's ancestors array. Removes
        default filtering on `type` field.
        """
        base_query = self.search.query()
        obj = super(CollectionViewSet, self).get_object()
        if self.request.GET.get("query"):
            for c in obj.children:
                q = Q("nested", path="ancestors", query=Q("match", ancestors__identifier=c.identifier))
                queryset = base_query.query(q)
                query_dict = self.filter_queryset(queryset).to_dict()
                query_dict["query"]["bool"].pop("filter", None)
                self.search.query = query_dict["query"]
                c.hit_count = self.search.query().count()
        return obj


class ObjectViewSet(DocumentViewSet, AncestorMixin):
    """
    Returns data about objects, or groups of archival records which have no children.
    """

    document = Object
    list_serializer = ObjectListSerializer
    serializer = ObjectSerializer

    filter_fields = {
        "title": {"field": "title.keyword", "lookups": STRING_LOOKUPS, },
        "start_date": {"field": "dates.begin", "lookups": NUMBER_LOOKUPS, },
        "end_date": {"field": "dates.end", "lookups": NUMBER_LOOKUPS, },
    }

    search_fields = ("title",)
    search_nested_fields = {
        "notes": {"path": "notes", "fields": ["subnotes.content"]},
    }

    ordering_fields = {
        "title": "title.keyword",
        "start_date": "dates.begin",
        "end_date": "dates.end",
    }


class TermViewSet(DocumentViewSet):
    """
    Returns data about terms, including subjects, geographic areas and more.
    """

    document = Term
    list_serializer = TermListSerializer
    serializer = TermSerializer

    filter_fields = {
        "title": {"field": "title.keyword", "lookups": STRING_LOOKUPS, },
        "term_type": {"field": "term_type", "lookups": STRING_LOOKUPS, },
    }

    search_fields = ("title", "type")

    ordering_fields = {
        "title": "title.keyword",
    }


class SearchView(DocumentViewSet):
    """Performs search queries across agents, collections, objects and terms."""
    document = BaseDescriptionComponent
    list_serializer = CollectionHitSerializer
    pagination_class = CollapseLimitOffsetPagination
    filter_backends = SEARCH_BACKENDS

    filter_fields = {
        "category": {"field": "category", "lookups": STRING_LOOKUPS},
        "end_date": {"field": "dates.end", "lookups": NUMBER_LOOKUPS},
        "genre": {"field": "formats", "lookups": STRING_LOOKUPS},
        "online": "online",
        "start_date": {"field": "dates.begin", "lookups": NUMBER_LOOKUPS},
        "type": {"field": "type", "lookups": STRING_LOOKUPS},
    }
    nested_filter_fields = {
        "subject": {
            "field": "terms.title.keyword",
            "path": "terms",
        },
        "creator": {
            "field": "creators.title.keyword",
            "path": "creators"
        }
    }
    ordering_fields = {
        "title": "group.title",
        "start_date": "group.dates.begin",
        "end_date": "group.dates.end",
        "creator": {
            "field": "group.creators.title.keyword",
            "path": "group.creators"
        }
    }
    search_fields = ("title", "description", "type", "")
    search_nested_fields = {
        "notes": {"path": "notes", "fields": ["subnotes.content"]},
    }

    def get_queryset(self):
        """Uses `collapse` to group hits based on `group` attribute."""
        collapse_params = {
            "field": "group.identifier",
            "inner_hits": {
                "size": 0,
                "name": "collection_hits",
                "_source": False
            }
        }
        a = A("cardinality", field="group.identifier")
        self.search.aggs.bucket("total", a)
        return self.search.extra(collapse=collapse_params).query()


class FacetView(SearchView):
    """Returns facets based on search terms."""
    serializer = FacetSerializer

    def get_queryset(self):
        """Adds aggregations and sets an empty size to return only facets."""
        creator = A("nested", path="creators")
        creator_name = A("terms", field="creators.title.keyword", size=100)
        subject = A("nested", path="terms")
        subject_name = A("terms", field="terms.title.keyword", size=100)
        format = A("terms", field="formats.keyword")
        max_date = A("max", field="dates.end", format="epoch_millis")
        min_date = A("min", field="dates.begin", format="epoch_millis")
        online = A('filter', Q('terms', online=[True]))
        self.search.aggs.bucket('creator', creator).bucket("name", creator_name)
        self.search.aggs.bucket('subject', subject).bucket("name", subject_name)
        self.search.aggs.bucket('format', format)
        self.search.aggs.bucket("max_date", max_date)
        self.search.aggs.bucket("min_date", min_date)
        self.search.aggs.bucket("online", online)
        return self.search.extra(size=0)

    def retrieve(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        results = queryset.execute()
        serializer = self.get_serializer(results)
        return Response(serializer.data)
