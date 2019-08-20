from django.http import Http404

from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from elasticsearch_dsl import connections, Index, Search

from django_elasticsearch_dsl_drf.constants import (
    LOOKUP_FILTER_TERMS,
    LOOKUP_FILTER_RANGE,
    LOOKUP_FILTER_PREFIX,
    LOOKUP_FILTER_WILDCARD,
    LOOKUP_QUERY_IN,
    LOOKUP_QUERY_GT,
    LOOKUP_QUERY_GTE,
    LOOKUP_QUERY_LT,
    LOOKUP_QUERY_LTE,
    LOOKUP_QUERY_EXCLUDE,
)
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    IdsFilterBackend,
    OrderingFilterBackend,
    DefaultOrderingFilterBackend,
    CompoundSearchFilterBackend,
)
from django_elasticsearch_dsl_drf.pagination import PageNumberPagination

from .elasticsearch.documents import Agent, Collection, Object, Term
from .serializers import (
    AgentSerializer, AgentListSerializer,
    CollectionSerializer, CollectionListSerializer,
    ObjectSerializer, ObjectListSerializer,
    TermSerializer, TermListSerializer
    )


class DocumentViewSet(ReadOnlyModelViewSet):
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
    document = Agent
    ordering_fields = {}

    def get_serializer_class(self):
        if self.action == 'list':
            return AgentListSerializer
        return AgentSerializer

    filter_backends = [
        FilteringFilterBackend,
        IdsFilterBackend,
        OrderingFilterBackend,
        CompoundSearchFilterBackend,
    ]

    filter_fields = {
        'id': {
            'field': 'id',
            'lookups': [
                LOOKUP_FILTER_RANGE,
                LOOKUP_QUERY_IN,
                LOOKUP_QUERY_GT,
                LOOKUP_QUERY_GTE,
                LOOKUP_QUERY_LT,
                LOOKUP_QUERY_LTE,
            ],
        },
        'title': 'title.raw',
        'type': 'type.raw',
    }


class CollectionViewSet(DocumentViewSet):
    document = Collection
    ordering_fields = {}

    def get_serializer_class(self):
        if self.action == 'list':
            return CollectionListSerializer
        return CollectionSerializer

    # TODO: filtering and ordering


class ObjectViewSet(DocumentViewSet):
    document = Object
    ordering_fields = {}

    def get_serializer_class(self):
        if self.action == 'list':
            return ObjectListSerializer
        return ObjectSerializer

    # TODO: filtering and ordering


class TermViewSet(DocumentViewSet):
    document = Term
    ordering_fields = {}

    def get_serializer_class(self):
        if self.action == 'list':
            return TermListSerializer
        return TermSerializer

    # TODO: filtering and ordering
