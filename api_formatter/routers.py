from rest_framework.routers import APIRootView, DefaultRouter


class RACAPIRootView(APIRootView):
    """Root of the Rockefeller Archive Center API."""
    name = "Rockefeller Archive Center API"

    def get(self, request, *args, **kwargs):
        """Adds additional endpoints."""
        self.api_root_dict.update([
            ('facets', 'facets'),
            ('mylist', 'mylist')])
        return super(RACAPIRootView, self).get(request, *args, **kwargs)


class RACRouter(DefaultRouter):
    APIRootView = RACAPIRootView
