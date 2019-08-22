from rest_framework.routers import DefaultRouter, APIRootView


class RACAPIRootView(APIRootView):
    """Root of the Rockefeller Archive Center API"""
    name = "Rockefeller Archive Center API"


class RACRouter(DefaultRouter):
    APIRootView = RACAPIRootView
