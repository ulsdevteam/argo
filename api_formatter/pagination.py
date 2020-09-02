from django_elasticsearch_dsl_drf.pagination import LimitOffsetPagination


class CollapseLimitOffsetPagination(LimitOffsetPagination):
    """Customized limit/offset pagination which handles collapsed results."""

    def get_paginated_response_context(self, data):
        """Get paginated response data.
        :param data:
        :return:
        """
        return [
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
        ]

    def get_count(self, es_response):
        if self.facets:
            return self.facets.total.value
        else:
            return super(LimitOffsetPagination, self).get_count(es_response)
