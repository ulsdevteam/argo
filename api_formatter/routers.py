from rest_framework.routers import DefaultRouter, APIRootView, Route


class RACAPIRootView(APIRootView):
    """Root of the Rockefeller Archive Center API"""
    name = "Rockefeller Archive Center API"

    def get(self, request, *args, **kwargs):
        # Add Search and Schema endpoints to API Root
        self.api_root_dict.update([('search', 'search'), ('schema', 'schema')])
        return super(RACAPIRootView, self).get(request, *args, **kwargs)


class RACRouter(DefaultRouter):
    APIRootView = RACAPIRootView
