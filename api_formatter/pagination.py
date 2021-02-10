from django_elasticsearch_dsl_drf.pagination import LimitOffsetPagination


class CollapseLimitOffsetPagination(LimitOffsetPagination):
    """Customized limit/offset pagination which handles collapsed results."""

    def get_paginated_response_context(self, data):
        """Overrides `get_paginated_response_context` to ignore facets."""

        return [
            ('count', self.get_count()),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
        ]

    def get_count(self):
        if self.facets:
            return self.facets.total.value
        else:
            return self.count
