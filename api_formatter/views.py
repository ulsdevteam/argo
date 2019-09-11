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
                return self.list_serializer
            except AttributeError:
                return self.serializer
        return self.serializer

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
            obj = hits[0]
            try:
                for relation in self.relations:
                    setattr(obj, relation[0], obj.get_references(relation=relation[1]))
            except AttributeError:
                pass
            return obj
        elif count > 1:
            raise Http404("Multiple results matches the given query. Expected a single result.")
        raise Http404("No result matches the given query.")


class AgentViewSet(DocumentViewSet):
    """
    Returns data about agents, including people, organizations and families.
    """
    document = Agent
    list_serializer = AgentListSerializer
    serializer = AgentSerializer
    relations = (
        ('collections', 'collection'),
        ('objects', 'object'),
    )

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


class CollectionViewSet(DocumentViewSet):
    """
    Returns data about collections, or intellectually significant groups of archival records.
    """
    document = Collection
    list_serializer = CollectionListSerializer
    serializer = CollectionSerializer
    relations = (
        ('ancestors', 'ancestor'),
        ('children', 'child'),
        ('terms', 'term'),
        ('agents', 'agent')
    )

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


class ObjectViewSet(DocumentViewSet):
    """
    Returns data about objects, or groups of archival records which have no children.
    """
    document = Object
    list_serializer = ObjectListSerializer
    serializer = ObjectSerializer
    relations = (
        ('ancestors', 'ancestor'),
        ('terms', 'term'),
        ('agents', 'agent'),
    )

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


class TermViewSet(DocumentViewSet):
    """
    Returns data about terms, including subjects, geographic areas and more.
    """
    document = Term
    list_serializer = TermListSerializer
    serializer = TermSerializer
    relations = (
        ('collections', 'collection'),
        ('objects', 'object'),
    )

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


class SearchView(DocumentViewSet):
    """
    Performs search queries across agents, collections, objects and terms.
    """

    list_serializer = HitSerializer
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
