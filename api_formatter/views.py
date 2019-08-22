from django.http import Http404
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from elasticsearch_dsl import connections, Index, Search

from .elasticsearch.documents import Agent, Collection, Object, Term
from .elasticsearch.view_helpers import STRING_LOOKUPS, NUMBER_LOOKUPS, FILTER_BACKENDS
from .serializers import (
    AgentSerializer, AgentListSerializer,
    CollectionSerializer, CollectionListSerializer,
    ObjectSerializer, ObjectListSerializer,
    TermSerializer, TermListSerializer
    )


class DocumentViewSet(ReadOnlyModelViewSet):
    filter_backends = FILTER_BACKENDS

    def __init__(self, *args, **kwargs):
        assert self.document is not None

        self.client = connections.get_connection(
            self.document._get_using()
        )
        self.index = self.document._index._name
        if not Index(self.index).exists():
            raise Http404("Index `{}` does not exist".format(self.index))
        self.mapping = self.document._doc_type.mapping.properties.name
        self.search = Search(
            using=self.client,
            index=self.index,
            doc_type=self.document._doc_type.name
        )
        super(ReadOnlyModelViewSet, self).__init__(*args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'list':
            return self.ListSerializer if self.ListSerializer else self.Serializer
        return self.Serializer

    def get_queryset(self):
        return self.search.query()

    def get_object(self):
        queryset = self.get_queryset()
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg not in self.kwargs:
            raise AttributeError("Expected view %s to be called with a URL keyword argument "
                                 "named '%s'. Fix your URL conf, or set the `.lookup_field` "
                                 "attribute on the view correctly." % (self.__class__.__name__, lookup_url_kwarg))
        queryset = queryset.filter('match_phrase', **{'_id': self.kwargs[lookup_url_kwarg]})
        hits = queryset.execute().hits.hits
        count = len(hits)
        if count == 1:
            return hits[0]['_source']
        elif count > 1:
            raise Http404("Multiple results matches the given query. Expected a single result.")
        raise Http404("No result matches the given query.")


class AgentViewSet(DocumentViewSet):
    """
    Returns data about agents, including people, organizations and families.
    """
    document = Agent
    ListSerializer = AgentListSerializer
    Serializer = AgentSerializer

    filter_fields = {
        'id': {
            'field': 'id',
            'lookups': STRING_LOOKUPS,
            },
        'title': {
            'field': 'title.raw',
            'lookups': STRING_LOOKUPS,
            },
        'description': {
            'title': 'description.raw',
            'lookups': STRING_LOOKUPS,
            },
        'type': {
            'title': 'type',
            'lookups': STRING_LOOKUPS,
            },
        'dates.begin': {
            'title': 'dates.begin',
            'lookups': NUMBER_LOOKUPS,
            },
        'dates.end': {
            'title': 'dates.end',
            'lookups': NUMBER_LOOKUPS,
            },
        }

    search_fields = ('title', 'description', 'notes.subnotes.content')

    ordering_fields = {
        'title': 'title.raw',
        'type': 'type.raw',
        'start_date': 'dates.begin',
        'end_date': 'dates.end',
    }


class CollectionViewSet(DocumentViewSet):
    """
    Returns data about collections, or intellectually significant groups of archival records.
    """
    document = Collection
    ListSerializer = CollectionListSerializer
    Serializer = CollectionSerializer

    filter_fields = {}

    search_fields = []

    ordering_fields = {}

    # TODO: filtering and ordering


class ObjectViewSet(DocumentViewSet):
    """
    Returns data about objects, or groups of archival records which have no children.
    """
    document = Object
    ListSerializer = ObjectListSerializer
    Serializer = ObjectSerializer

    filter_fields = {}

    search_fields = []

    ordering_fields = {}

    # TODO: filtering and ordering


class TermViewSet(DocumentViewSet):
    """
    Returns data about terms, including subjects, geographic areas and more.
    """
    document = Term
    ListSerializer = TermListSerializer
    Serializer = TermSerializer

    filter_fields = {}

    search_fields = []

    ordering_fields = {}

    # TODO: filtering and ordering
