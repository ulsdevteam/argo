from django.http import Http404
from elasticsearch_dsl import DateHistogramFacet
from rac_es.documents import Agent, Collection, Object, Term
from rest_framework.viewsets import ReadOnlyModelViewSet

from .serializers import (AgentListSerializer, AgentSerializer,
                          CollectionListSerializer, CollectionSerializer,
                          HitSerializer, ObjectListSerializer,
                          ObjectSerializer, TermListSerializer, TermSerializer)
from .view_helpers import (FILTER_BACKENDS, NUMBER_LOOKUPS, SEARCH_BACKENDS,
                           STRING_LOOKUPS, SearchMixin)


class DocumentViewSet(SearchMixin, ReadOnlyModelViewSet):
    filter_backends = FILTER_BACKENDS

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
        if self.request.GET.get("limit"):
            query = query[:int(self.request.GET.get("limit"))].execute()
        return query

    def get_object(self):
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
            obj = hits[0]
            return obj

    @property
    def list_fields(self):
        return list(set(list(self.filter_fields) + list(self.ordering_fields) + list(self.search_fields) + ["type", "dates"]))


class AgentViewSet(DocumentViewSet):
    """
    Returns data about agents, including people, organizations and families.
    """

    document = Agent
    list_serializer = AgentListSerializer
    serializer = AgentSerializer
    relations = ("collections", "objects")

    filter_fields = {
        "id": {"field": "id", "lookups": STRING_LOOKUPS, },
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


class CollectionViewSet(DocumentViewSet):
    """
    Returns data about collections, or intellectually significant groups of archival records.
    """

    document = Collection
    list_serializer = CollectionListSerializer
    serializer = CollectionSerializer
    relations = ("ancestors", "children", "creators", "terms", "agents")

    filter_fields = {
        "id": {"field": "id", "lookups": STRING_LOOKUPS, },
        "title": {"field": "title.keyword", "lookups": STRING_LOOKUPS, },
        "start_date": {"field": "dates.begin", "lookups": NUMBER_LOOKUPS, },
        "end_date": {"field": "dates.end", "lookups": NUMBER_LOOKUPS, },
        "level": {"field": "level.keyword", "lookups": STRING_LOOKUPS, },
        "ancestors": "ancestors"
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


class ObjectViewSet(DocumentViewSet):
    """
    Returns data about objects, or groups of archival records which have no children.
    """

    document = Object
    list_serializer = ObjectListSerializer
    serializer = ObjectSerializer
    relations = ("ancestors", "terms", "agents")

    filter_fields = {
        "id": {"field": "id", "lookups": STRING_LOOKUPS, },
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
    relations = (
        "collections",
        "objects",
    )

    filter_fields = {
        "id": {"field": "id", "lookups": STRING_LOOKUPS, },
        "title": {"field": "title.keyword", "lookups": STRING_LOOKUPS, },
        "term_type": {"field": "term_type", "lookups": STRING_LOOKUPS, },
    }

    search_fields = ("title", "type")

    ordering_fields = {
        "title": "title.keyword",
    }


class SearchView(DocumentViewSet):
    """
    Performs search queries across agents, collections, objects and terms.
    """

    list_serializer = HitSerializer
    filter_backends = SEARCH_BACKENDS

    # TODO: determine if we need filter fields here
    filter_fields = {}  # This requires a mapping
    ordering_fields = {"title": "title.keyword", "type": "type.keyword"}
    search_fields = ("title", "description", "type", "")
    faceted_search_fields = {
        "type": "type.keyword",
        "start_date": {
            "field": "dates.begin",
            "facet": DateHistogramFacet,
            "options": {"interval": "year", },
        },
        "end_date": {
            "field": "dates.end",
            "facet": DateHistogramFacet,
            "options": {"interval": "year", },
        },
    }
    search_nested_fields = {
        "notes": {"path": "notes", "fields": ["subnotes.content"]},
    }

    def get_queryset(self):
        return self.search.query()
