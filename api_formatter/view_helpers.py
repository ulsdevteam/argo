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
                                                          FilteringFilterBackend,
                                                          NestedFilteringFilterBackend,
                                                          OrderingFilterBackend)
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


class CustomOrderingBackend(OrderingFilterBackend):

    @classmethod
    def transform_ordering_params(cls, ordering_params, ordering_fields):
        """Overrides existing transform_ordering_params method, which presumes
        that all nested sort paths are completely nested.

        This code could be removed if https://github.com/barseghyanartur/django-elasticsearch-dsl-drf/issues/212 is addressed.
        """
        _ordering_params = []
        for ordering_param in ordering_params:
            key = ordering_param.lstrip('-')
            direction = 'desc' if ordering_param.startswith('-') else 'asc'
            if key in ordering_fields:
                field = ordering_fields[key]
                entry = {
                    field['field']: {
                        'order': direction,
                    }
                }
                if 'path' in field:
                    entry[field['field']].update(
                        {"nested": {"path": field["path"]}})  # this is the line that has changed
                _ordering_params.append(entry)
        return _ordering_params


FILTER_BACKENDS = [FilteringFilterBackend,
                   CustomOrderingBackend,
                   DefaultOrderingFilterBackend,
                   CompoundSearchFilterBackend]

SEARCH_BACKENDS = FILTER_BACKENDS + [NestedFilteringFilterBackend, ]
