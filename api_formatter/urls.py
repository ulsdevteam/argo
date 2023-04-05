from django.urls import include, re_path
from rest_framework.schemas import get_schema_view

from .routers import RACRouter
from .views import (AgentViewSet, CollectionViewSet, FacetView, ObjectViewSet,
                    SearchView, TermViewSet)

router = RACRouter(trailing_slash=False)
router.register(r'agents', AgentViewSet, basename='agent')
router.register(r'collections', CollectionViewSet, basename='collection')
router.register(r'objects', ObjectViewSet, basename='object')
router.register(r'terms', TermViewSet, basename='term')
router.register(r'search', SearchView, basename='search')

schema_view = get_schema_view(
    title="Rockefeller Archive Center Collections API",
    description="The Rockefeller Archive Center Collections API provides data about the archival collections we hold and the individuals and organizations associated with them.",
    version="1.0.0",
    patterns=router.urls,
)

urlpatterns = [
    re_path(r'^', include(router.urls)),
    re_path(r'facets$', FacetView.as_view({'get': 'retrieve'}), name='facets'),
    re_path(r'schema$', schema_view, name='schema'),
]
