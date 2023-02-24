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
from django_elasticsearch_dsl_drf.filter_backends import (
    DefaultOrderingFilterBackend, FilteringFilterBackend,
    NestedFilteringFilterBackend, OrderingFilterBackend,
    SuggesterFilterBackend)
from django_elasticsearch_dsl_drf.pagination import LimitOffsetPagination
from elasticsearch_dsl import Index, Search, connections
from rest_framework.viewsets import ReadOnlyModelViewSet

from argo import settings

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
        if issubclass(type(self), ReadOnlyModelViewSet):
            super(ReadOnlyModelViewSet, self).__init__(*args, **kwargs)


class CustomFilteringFilterBackend(FilteringFilterBackend):
    """Provides search filter parameters to schema."""

    def get_schema_operation_parameters(self, view):
        params = []
        for filter_param in view.filter_fields:
            params.append(
                {
                    'name': filter_param,
                    'required': False,
                    'in': 'query',
                    'description': f'Filter results by {filter_param}.',
                    'schema': {
                        'type': 'string',
                    },
                }
            )
        params.append(
            {
                'name': settings.REST_FRAMEWORK["SEARCH_PARAM"],
                'required': False,
                'in': 'query',
                'description': 'Query string for full-text search.',
                'schema': {
                    'type': 'string',
                },
            }
        )
        return params


class CustomOrderingFilterBackend(OrderingFilterBackend):
    """Provides ordering parameters to schema."""

    def get_schema_operation_parameters(self, view):
        sort_fields = ", ".join([f for f in view.ordering_fields])
        return [
            {
                'name': self.ordering_param,
                'required': False,
                'in': 'query',
                'description': f'Sort results by {sort_fields}.  By default the named property will be sorted ascending. Descending order can be achieved by appending a - to the start of the property.',
                'schema': {
                    'type': 'string',
                },
            }]


FILTER_BACKENDS = [CustomFilteringFilterBackend,
                   CustomOrderingFilterBackend,
                   DefaultOrderingFilterBackend]

FILTER_FIELDS = {
    "category": {"field": "category", "lookups": STRING_LOOKUPS},
    "end_date": {"field": "dates.end", "lookups": NUMBER_LOOKUPS},
    "genre": {"field": "formats.keyword", "lookups": STRING_LOOKUPS},
    "start_date": {"field": "dates.begin", "lookups": NUMBER_LOOKUPS},
}

NESTED_FILTER_FIELDS = {
    "subject": {
        "field": "terms.title.keyword",
        "path": "terms",
    },
    "creator": {
        "field": "creators.title.keyword",
        "path": "creators"
    }
}

SEARCH_FIELDS = ("title",)
SEARCH_NESTED_FIELDS = {
    "notes": {"path": "notes", "fields": ["subnotes.content"]},
}

ORDERING_FIELDS = {
    "title": "title.keyword",
    "start_date": "dates.begin",
    "end_date": "dates.end",
}

SEARCH_BACKENDS = FILTER_BACKENDS + [NestedFilteringFilterBackend, SuggesterFilterBackend]


class ChildrenPaginator(LimitOffsetPagination):

    def paginate_queryset(self, queryset, request):
        """Custom method to paginate lists of children."""
        self.request = request
        self.limit = int(self.request.GET["limit"]) if self.request.GET.get("limit") else settings.REST_FRAMEWORK["PAGE_SIZE"]
        self.offset = int(self.request.GET["offset"]) if self.request.GET.get("offset") else 0
        self.count = queryset.count()
        if self.count == 0 or self.offset > self.count:
            return []
        return list(queryset[self.offset:self.offset + self.limit])


def text_from_notes(notes, note_type):
    """Returns a content string for a specific note from an array of notes.

    Args:
        notes (list): note list
        note_type (str): note type
    """
    description_strings = []
    for note in [n for n in notes if n["type"] == note_type]:
        description_strings += [" ".join(sn["content"]) for sn in note["subnotes"]]
    return " ".join(description_strings) if description_strings else None


def date_string(dates):
    """Returns a date string from an array of dates."""
    date_strings = []
    for date in dates:
        try:
            expression = date["expression"]
        except KeyError:
            if date.get("end"):
                expression = "{0}-{1}".format(date["begin"], date["end"])
            else:
                expression = date["begin"]
        date_strings.append(expression)
    return ", ".join(date_strings)


def description_from_notes(notes):
    return text_from_notes(notes, "abstract") if text_from_notes(notes, "abstract") else text_from_notes(notes, "scopecontent")
