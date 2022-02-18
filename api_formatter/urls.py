from django.conf.urls import include, url
from rest_framework.schemas import get_schema_view

from .routers import RACRouter
from .views import (AgentViewSet, CollectionViewSet, FacetView, ObjectViewSet,
                    SearchView)

router = RACRouter(trailing_slash=False)
router.register(r'agents', AgentViewSet, basename='agent')
router.register(r'collections', CollectionViewSet, basename='collection')
router.register(r'objects', ObjectViewSet, basename='object')
router.register(r'search', SearchView, basename='search')

schema_view = get_schema_view(
    title="Rockefeller Archive Center Collections API",
    description="The Rockefeller Archive Center Collections API provides data about the archival collections we hold and the individuals and organizations associated with them.",
    version="1.0.0",
    patterns=router.urls,
)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'facets', FacetView.as_view({'get': 'retrieve'}), name='facets'),
    url(r'^schema', schema_view, name='schema'),
]
