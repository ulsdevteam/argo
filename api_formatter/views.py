from argo import settings
from django.http import Http404
from django_elasticsearch_dsl_drf.constants import SUGGESTER_TERM
from django_elasticsearch_dsl_drf.pagination import LimitOffsetPagination
from elasticsearch_dsl import A, Q
from rac_es.documents import (Agent, BaseDescriptionComponent, Collection,
                              Object, Term)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from .pagination import CollapseLimitOffsetPagination
from .serializers import (AgentListSerializer, AgentSerializer,
                          AncestorsSerializer, CollectionHitSerializer,
                          CollectionListSerializer, CollectionSerializer,
                          FacetSerializer, ObjectListSerializer,
                          ObjectSerializer, ReferenceSerializer,
                          TermListSerializer, TermSerializer)
from .view_helpers import (FILTER_BACKENDS, FILTER_FIELDS,
                           NESTED_FILTER_FIELDS, NUMBER_LOOKUPS,
                           ORDERING_FIELDS, SEARCH_BACKENDS, SEARCH_FIELDS,
                           SEARCH_NESTED_FIELDS, STRING_LOOKUPS,
                           ChildrenPaginator, SearchMixin, date_string,
                           description_from_notes)


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
            data = self.get_object_data(Collection, a.identifier)
            a.dates = data["dates"]
            a.description = data["description"]
            a.online = data["online"]
            a.title = data["title"]
            if len(self.request.GET):
                a.hit_count, a.online_hit_count = self.get_hit_counts(a.identifier, base_query)
        serializer = AncestorsSerializer(ancestors)
        return Response(serializer.data)


class ObjectResolverMixin(object):
    """Provides a `resolve_object` method, which returns an object based on object type and identifier."""

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
            raise Http404("No object matches the given query.")
        else:
            return hits[0]


class DocumentViewSet(SearchMixin, ObjectResolverMixin, ReadOnlyModelViewSet):
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
        return query.source(excludes=["ancestors", "children"])

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

    def get_object_data(self, object_type, identifier):
        """Gets additional data from an object.

        Returns a dict containing a date string, text from Abstracts or Scope
        and Contents notes and a boolean indicator of a digital surrogate.
        """
        data = {"dates": None, "description": None, "online": False, "title": None}
        try:
            resolved = self.resolve_object(object_type, identifier, source_fields=["dates", "notes", "online", "title"])
            data["description"] = description_from_notes(resolved.to_dict().get("notes", []))
            data["online"] = getattr(resolved, "online", False)
            data["dates"] = date_string(resolved.to_dict().get("dates", []))
            data["title"] = resolved.title
            return data
        except Http404:
            return data

    def get_hit_counts(self, uri, base_query):
        """Gets the number of hits that are children of a specific component.

        If no query string exists in the request, returns None. If the query
        filters on an object, removes that portion of the query so that results
        for all object types are returned.
        """
        if self.request.GET.get(settings.REST_FRAMEWORK["SEARCH_PARAM"]):
            identifier = uri.lstrip("/").split("/")[-1]
            q = Q("nested", path="ancestors", query=Q("match", ancestors__identifier=identifier)) | Q("ids", values=[identifier])
            queryset = base_query.query(self.get_structured_query()).query(q)
            query_dict = self.filter_queryset(queryset).to_dict()
            # remove type from query, which limits results to the document type
            if query_dict["query"]["bool"].get("filter"):
                processed_filter = list(filter(lambda i: "term" not in i, query_dict["query"]["bool"]["filter"]))
                query_dict["query"]["bool"]["filter"] = processed_filter
            self.search.query = query_dict["query"]
            hit_count = self.search.query().count()
            query_dict["query"]["bool"]["filter"] = [{"term": {"online": True}}]
            self.search.query = query_dict["query"]
            online_hit_count = self.search.query().count()
            return hit_count, online_hit_count
        return None, None

    def get_structured_query(self):
        """Returns default query structure."""

        query = self.request.GET.get(settings.REST_FRAMEWORK["SEARCH_PARAM"])
        return Q("bool",
                 should=[
                     Q("simple_query_string",
                         analyze_wildcard=True,
                         query=query,
                         fields=["title^5", "description"],
                         default_operator="and"),
                     Q("nested",
                         path="notes",
                         query=Q("simple_query_string",
                                 analyze_wildcard=True,
                                 query=query,
                                 fields=["notes.subnotes.content"],
                                 default_operator="and")),
                     Q("nested",
                         path="terms",
                         query=Q("simple_query_string",
                                 analyze_wildcard=True,
                                 query=query,
                                 fields=["terms.title"],
                                 default_operator="and"))])

    @property
    def list_fields(self):
        return list(set(list(self.filter_fields) + list(self.ordering_fields) + list(self.search_fields) + ["type", "dates"]))


class AgentViewSet(DocumentViewSet):
    """Returns data about agents, including people, organizations and families."""

    document = Agent
    list_serializer = AgentListSerializer
    serializer = AgentSerializer

    filter_fields = {
        "title": {"field": "title.keyword", "lookups": STRING_LOOKUPS, },
        "agent_type": {"field": "agent_type", "lookups": STRING_LOOKUPS, },
        "start_date": {"field": "dates.begin", "lookups": NUMBER_LOOKUPS, },
        "end_date": {"field": "dates.end", "lookups": NUMBER_LOOKUPS, },
    }
    search_fields = SEARCH_FIELDS + ("description",)
    search_nested_fields = SEARCH_NESTED_FIELDS
    ordering_fields = {**ORDERING_FIELDS, **{"type": "type.keyword"}}


class CollectionViewSet(DocumentViewSet, AncestorMixin):
    """Returns data about collections, or intellectually significant groups of archival records."""

    document = Collection
    list_serializer = CollectionListSerializer
    serializer = CollectionSerializer
    filter_backends = SEARCH_BACKENDS

    filter_fields = FILTER_FIELDS
    nested_filter_fields = NESTED_FILTER_FIELDS
    search_fields = SEARCH_FIELDS
    search_nested_fields = SEARCH_NESTED_FIELDS
    ordering_fields = ORDERING_FIELDS

    def prepare_children(self, children, group, base_query):
        """Appends additional data to each child object.

        Adds `group` information from the parent collection, along with strings
        for dates and description.

        If a query parameter exists, fetches the hit count.
        """
        for c in children:
            c.group = group  # append group from parent collection
            c.dates = date_string(c.to_dict().get("dates", []))
            c.description = description_from_notes(c.to_dict().get("notes", []))
            if len(self.request.GET):
                c.hit_count, c.online_hit_count = self.get_hit_counts(c.uri, base_query)
        return children

    @action(detail=True)
    def children(self, request, pk=None):
        """Provides a detail endpoint for a collection's children."""
        base_query = self.search.query()
        self.search.query = Q("match_phrase", parent=pk)
        child_hits = self.search.source(
            ["group", "type", "uri", "dates", "notes", "online", "position", "title"]
        ).sort("position")
        obj = self.resolve_object(Collection, pk, source_fields=["group"])
        paginator = ChildrenPaginator()
        page = paginator.paginate_queryset(child_hits, request)
        if page is not None:
            page = self.prepare_children(page, obj.group, base_query)
            serializer = ReferenceSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        children = self.prepare_children(child_hits, obj.group, base_query)
        serializer = ReferenceSerializer(children, many=True)
        return paginator.get_paginated_response(serializer.data)


class ObjectViewSet(DocumentViewSet, AncestorMixin):
    """Returns data about objects, or groups of archival records without children."""

    document = Object
    list_serializer = ObjectListSerializer
    serializer = ObjectSerializer
    filter_backends = SEARCH_BACKENDS
    filter_fields = FILTER_FIELDS
    nested_filter_fields = NESTED_FILTER_FIELDS
    search_fields = SEARCH_FIELDS
    search_nested_fields = SEARCH_NESTED_FIELDS
    ordering_fields = ORDERING_FIELDS


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

    search_fields = SEARCH_FIELDS + ("type",)

    ordering_fields = {
        "title": "title.keyword",
    }


class SearchView(DocumentViewSet):
    """Performs search queries across agents, collections, objects and terms."""
    document = BaseDescriptionComponent
    serializer = CollectionHitSerializer
    pagination_class = CollapseLimitOffsetPagination
    filter_backends = SEARCH_BACKENDS
    filter_fields = {**FILTER_FIELDS, **{"type": {"field": "type", "lookups": STRING_LOOKUPS}}}
    nested_filter_fields = NESTED_FILTER_FIELDS
    search_fields = SEARCH_FIELDS
    search_nested_fields = SEARCH_NESTED_FIELDS
    suggester_fields = {
        "title_suggest": {
            "field": "title",
            "suggesters": [SUGGESTER_TERM],
            "default_suggester": SUGGESTER_TERM,
        }
    }
    ordering_fields = {** ORDERING_FIELDS, **{
        "creator": {
            "field": "group.creators.title.keyword",
            "path": "group.creators",
            "split_path": False,
        }
    }}

    def get_queryset(self):
        """Sets up base params for search.

        Uses `collapse` to group hits based on `group.identifier` attribute.
        Adds a `cardinality` aggregation to get the total count of grouped
        results, and finally appends the structured query."""

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
        return (self.search.extra(collapse=collapse_params).query(self.get_structured_query())
                if self.request.GET.get(settings.REST_FRAMEWORK["SEARCH_PARAM"])
                else self.search.extra(collapse=collapse_params).query())

    def list(self, request, *args, **kwargs):
        """Overrides default `list` behavior to add `hit_count` and `online_hit_count` attributes."""

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            for p in page:
                p.hit_count, p.online_hit_count = self.get_hit_counts(p.group.identifier, queryset)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        for q in queryset:
            q.hit_count, q.online_hit_count = self.get_hit_counts(q.uri, queryset)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def suggest(self, request):
        """Suggest functionality."""
        queryset = self.filter_queryset(self.get_queryset())
        is_suggest = getattr(queryset, '_suggest', False)
        if not is_suggest:
            return Response(
                status=HTTP_400_BAD_REQUEST
            )
        page = self.paginate_queryset(queryset)
        return Response(page)


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
        return (self.search.extra(size=0).query(self.get_structured_query())
                if self.request.GET.get(settings.REST_FRAMEWORK["SEARCH_PARAM"])
                else self.search.extra(size=0))

    def retrieve(self, request, *args, **kwargs):
        results = self.get_queryset().execute()
        serializer = self.get_serializer(results)
        return Response(serializer.data)


class MyListView(SearchMixin, ObjectResolverMixin, APIView):
    """Returns a formatted MyList view.

    Takes a list of URIs, resolves saved items, and groups them by collection.
    """

    def post(self, request, format=None):
        list = request.data.get("list", [])
        resp = []
        resolved_list = []
        for uri in list:
            object_type, ident = uri.lstrip("/").split("/")
            try:
                resolved = self.resolve_object(Collection if object_type == "collection" else Object, ident,
                                               source_fields=["ancestors", "title", "uri", "dates", "extents",
                                                              "group", "notes", "online", "external_identifiers"])
                resolved_list.append(resolved)
            except Http404:
                pass  # missing objects are ignored
        collection_titles = set(map(lambda x: x.group.title, resolved_list))
        for title in collection_titles:
            collection_objects = [obj.to_dict() for obj in resolved_list if obj.group.title == title]
            items = [
                {
                    "title": obj["title"],
                    "uri": obj["uri"],
                    "dates": date_string(obj.get("dates", [])),
                    "description": description_from_notes(obj.get("notes", [])),
                    "extents": obj.get("extents"),
                    "notes": [note for note in obj.get("notes", []) if note["type"] in ["scopecontent", "abstract"]],
                    "parent": obj["ancestors"][0]["title"],
                    "parent_ref": "/collections/{}".format(obj["ancestors"][0]["identifier"]),
                    "online": obj["online"],
                    "archivesspace_uri": [ident["identifier"] for ident in obj["external_identifiers"] if ident["source"] == "archivesspace"][0]
                } for obj in collection_objects]
            resp.append({"title": title, "items": items})
        return Response(resp)
