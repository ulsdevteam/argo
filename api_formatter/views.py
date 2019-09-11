from django.http import Http404
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from elasticsearch_dsl import connections, Index, Search, DateHistogramFacet, RangeFacet, TermsFacet

from .elasticsearch.documents import Agent, Collection, Object, Term
from .view_helpers import (
    STRING_LOOKUPS,
    NUMBER_LOOKUPS,
    FILTER_BACKENDS,
    SEARCH_BACKENDS,
    PAGINATION_CLASS)
from .serializers import (
    HitSerializer,
    AgentSerializer, AgentListSerializer,
    CollectionSerializer, CollectionListSerializer,
    ObjectSerializer, ObjectListSerializer,
    TermSerializer, TermListSerializer)


class DocumentViewSet(ReadOnlyModelViewSet):
    filter_backends = FILTER_BACKENDS
    pagination_class = PAGINATION_CLASS

    def __init__(self, *args, **kwargs):
        assert self.document is not None

        self.client = connections.get_connection(
            self.document._get_using()
        )
        self.index = self.document._index._name
        if not Index(self.index).exists():
            raise Http404("Index `{}` does not exist".format(self.index))
        self.mapping = self.document._doc_type.mapping.properties.name
        self.search = self.document.search(
            using=self.client,
            # index=self.index,
            # doc_type=self.document._doc_type.name
        )
        super(ReadOnlyModelViewSet, self).__init__(*args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'list':
            try:
                return self.ListSerializer
            except AttributeError:
                return self.Serializer
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
        hits = queryset.execute().hits
        count = len(hits)
        if count == 1:
            # TODO: roll up fields which require resolution
            return hits[0]
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
            'field': 'title.keyword',
            'lookups': STRING_LOOKUPS,
            },
        'description': {
            'field': 'description.keyword',
            'lookups': STRING_LOOKUPS,
            },
        'agent_type': {
            'field': 'agent_type',
            'lookups': STRING_LOOKUPS,
            },
        'start_date': {
            'field': 'dates.begin',
            'lookups': NUMBER_LOOKUPS,
            },
        'end_date': {
            'field': 'dates.end',
            'lookups': NUMBER_LOOKUPS,
            },
        }

    search_fields = ('title', 'description')
    search_nested_fields = {
        'notes': {
            'path': 'notes',
            'fields': ['subnotes.content']
        },
    }

    ordering_fields = {
        'title': 'title.keyword',
        'type': 'type.keyword',
        'start_date': 'dates.begin',
        'end_date': 'dates.end',
    }

    def get_object(self):
        obj = super(AgentViewSet, self).get_object()
        obj.collections = obj.get_references(relation='collection')
        obj.objects = obj.get_references(relation='object')
        return obj


class CollectionViewSet(DocumentViewSet):
    """
    Returns data about collections, or intellectually significant groups of archival records.
    """
    document = Collection
    ListSerializer = CollectionListSerializer
    Serializer = CollectionSerializer

    filter_fields = {
        'id': {
            'field': 'id',
            'lookups': STRING_LOOKUPS,
            },
        'title': {
            'field': 'title.keyword',
            'lookups': STRING_LOOKUPS,
            },
        'start_date': {
            'field': 'dates.begin',
            'lookups': NUMBER_LOOKUPS,
            },
        'end_date': {
            'field': 'dates.end',
            'lookups': NUMBER_LOOKUPS,
            },
        'level': {
            'field': 'level.keyword',
            'lookups': STRING_LOOKUPS,
        },
    }

    search_fields = ('title',)
    search_nested_fields = {
        'notes': {
            'path': 'notes',
            'fields': ['subnotes.content']
        },
    }

    ordering_fields = {
        'title': 'title.keyword',
        'level': 'level.keyword',
        'start_date': 'dates.begin',
        'end_date': 'dates.end',
    }

    def get_object(self):
        obj = super(CollectionViewSet, self).get_object()
        obj.ancestors = obj.get_references(relation='ancestor')
        obj.children = obj.get_references(relation='child')
        obj.terms = obj.get_references(relation='term')
        obj.agents = obj.get_references(relation='agent')
        return obj


class ObjectViewSet(DocumentViewSet):
    """
    Returns data about objects, or groups of archival records which have no children.
    """
    document = Object
    ListSerializer = ObjectListSerializer
    Serializer = ObjectSerializer

    filter_fields = {
        'id': {
            'field': 'id',
            'lookups': STRING_LOOKUPS,
            },
        'title': {
            'field': 'title.keyword',
            'lookups': STRING_LOOKUPS,
            },
        'start_date': {
            'field': 'dates.begin',
            'lookups': NUMBER_LOOKUPS,
            },
        'end_date': {
            'field': 'dates.end',
            'lookups': NUMBER_LOOKUPS,
            },
        }

    search_fields = ('title',)
    search_nested_fields = {
        'notes': {
            'path': 'notes',
            'fields': ['subnotes.content']
        },
    }

    ordering_fields = {
        'title': 'title.keyword',
        'start_date': 'dates.begin',
        'end_date': 'dates.end',
    }

    def get_object(self):
        obj = super(ObjectViewSet, self).get_object()
        obj.ancestors = obj.get_references(relation='ancestor')
        obj.terms = obj.get_references(relation='term')
        obj.agents = obj.get_references(relation='agent')
        return obj


class TermViewSet(DocumentViewSet):
    """
    Returns data about terms, including subjects, geographic areas and more.
    """
    document = Term
    ListSerializer = TermListSerializer
    Serializer = TermSerializer

    filter_fields = {
        'id': {
            'field': 'id',
            'lookups': STRING_LOOKUPS,
            },
        'title': {
            'field': 'title.keyword',
            'lookups': STRING_LOOKUPS,
            },
        'term_type': {
            'field': 'term_type',
            'lookups': STRING_LOOKUPS,
            },
        }

    search_fields = ('title', 'type')

    ordering_fields = {
        'title': 'title.keyword',
    }

    def get_object(self):
        obj = super(TermViewSet, self).get_object()
        obj.collections = obj.get_references(relation='collection')
        obj.objects = obj.get_references(relation='object')
        return obj


class SearchView(DocumentViewSet):
    """
    Performs search queries across agents, collections, objects and terms.
    """

    # TODO: consider returning a query for each index,
    # which can then be handled by a different serializer and presented in
    # an array like {agents: [{...}], collections: [{...}], objects[{...}], terms: [{...}]}
    # We may want collections and objects returned in a single query but the other stuff
    # in separate arrays...

    ListSerializer = HitSerializer
    pagination_class = PAGINATION_CLASS
    filter_backends = SEARCH_BACKENDS

    # TODO: determine if we need filter fields here
    filter_fields = {}  # This requires a mapping
    ordering_fields = {'title': 'title.keyword', 'type': 'type.keyword'}
    search_fields = ('title', 'description', 'type', '')
    faceted_search_fields = {
        'type': 'type.keyword',
        'start_date': {
            'field': 'dates.begin',
            'facet': DateHistogramFacet,
            'options': {
                'interval': 'year',
            }
        },
        'end_date': {
            'field': 'dates.end',
            'facet': DateHistogramFacet,
            'options': {
                'interval': 'year',
            }
        }
    }
    search_nested_fields = {
        'notes': {
            'path': 'notes',
            'fields': ['subnotes.content']
        },
    }

    def __init__(self, *args, **kwargs):
        indices = ['default']
        if not Index(indices).exists():
            raise Http404("Index `{}` does not exist".format(indices))
        self.client = connections.get_connection('default')
        # TODO: will have to pass a mapping here
        # self.mapping = self.document._doc_type.mapping.properties.name
        self.search = Search(
            using=self.client,
            index=indices,
            doc_type=['_all']
        )
        super(DocumentViewSet, self).__init__(*args, **kwargs)

    def get_queryset(self):
        return self.search.query()
