from django.conf.urls import url, include
from rest_framework.schemas import get_schema_view
from rest_framework.routers import DefaultRouter

from .views import AgentViewSet, CollectionViewSet, ObjectViewSet, TermViewSet

router = DefaultRouter()
router.register(r'agents', AgentViewSet, basename='agent')
router.register(r'collections', CollectionViewSet, basename='collection')
router.register(r'objects', ObjectViewSet, basename='object')
router.register(r'terms', TermViewSet, basename='term')

schema_view = get_schema_view(
  title="Rockefeller Archive Center API",
  description="API for Rockefeller Archive Center data.",
)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^schema', schema_view, name='schema'),
]
