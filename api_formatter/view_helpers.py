from argo import settings
from django.http import Http404
from django_elasticsearch_dsl_drf.constants import (LOOKUP_FILTER_PREFIX,
                                                    LOOKUP_FILTER_RANGE,
                                                    LOOKUP_FILTER_TERMS,
                                                    LOOKUP_FILTER_WILDCARD,
                                                    LOOKUP_QUERY_EXCLUDE,
                                                    LOOKUP_QUERY_GT,
                                                    LOOKUP_QUERY_GTE,
                                                    LOOKUP_QUERY_IN,
                                                    LOOKUP_QUERY_LT,
                                                    LOOKUP_QUERY_LTE)
from django_elasticsearch_dsl_drf.filter_backends import (CompoundSearchFilterBackend,
                                                          DefaultOrderingFilterBackend,
                                                          FacetedSearchFilterBackend,
                                                          FilteringFilterBackend,
                                                          OrderingFilterBackend)
from django_elasticsearch_dsl_drf.pagination import PageNumberPagination
from elasticsearch_dsl import Index, Search, connections
from rest_framework.viewsets import ReadOnlyModelViewSet

STRING_LOOKUPS = [
    LOOKUP_FILTER_TERMS,
    LOOKUP_FILTER_PREFIX,
    LOOKUP_FILTER_WILDCARD,
    LOOKUP_QUERY_IN,
    LOOKUP_QUERY_EXCLUDE,
]

NUMBER_LOOKUPS = [
    LOOKUP_FILTER_RANGE,
    LOOKUP_QUERY_IN,
    LOOKUP_QUERY_GT,
    LOOKUP_QUERY_GTE,
    LOOKUP_QUERY_LT,
    LOOKUP_QUERY_LTE,
]

FILTER_BACKENDS = [FilteringFilterBackend,
                   OrderingFilterBackend,
                   DefaultOrderingFilterBackend,
                   CompoundSearchFilterBackend,
                   ]

SEARCH_BACKENDS = FILTER_BACKENDS + [FacetedSearchFilterBackend]

PAGINATION_CLASS = PageNumberPagination


class SearchMixin:
    """Mixin that provides a search object for views."""

    def __init__(self, *args, **kwargs):
        self.index = settings.ELASTICSEARCH_DSL['default']['index']
        self.client = connections.get_connection(
            settings.ELASTICSEARCH_DSL['default']['connection']
        )
        if not Index(self.index).exists():
            raise Http404("Index `{}` does not exist".format(self.index))
        try:
            self.mapping = self.document._doc_type.mapping.properties.name
            self.search = self.document.search(using=self.client)
        except AttributeError:
            self.search = Search(
                using=self.client,
                index=self.index,
                doc_type=['_all']
            )
        super(ReadOnlyModelViewSet, self).__init__(*args, **kwargs)
