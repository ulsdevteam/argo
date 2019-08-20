from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from .views import AgentViewSet, ObjectViewSet, TermViewSet

router = DefaultRouter()
router.register(r'agents', AgentViewSet, basename='agent')
router.register(r'objects', ObjectViewSet, basename='object')
router.register(r'terms', TermViewSet, basename='term')

# TODO: OpenAPI schema

urlpatterns = [
    url(r'^', include(router.urls)),
]
