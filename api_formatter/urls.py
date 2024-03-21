from django.urls import include, re_path

from .routers import RACRouter
from .views import (AgentViewSet, CollectionViewSet, FacetView, ObjectViewSet,
                    SearchView, TermViewSet)

router = RACRouter(trailing_slash=False)
router.register(r'agents', AgentViewSet, basename='agent')
router.register(r'collections', CollectionViewSet, basename='collection')
router.register(r'objects', ObjectViewSet, basename='object')
router.register(r'terms', TermViewSet, basename='term')
router.register(r'search', SearchView, basename='search')

urlpatterns = [
    re_path(r'^', include(router.urls)),
    re_path(r'facets$', FacetView.as_view({'get': 'retrieve'}), name='facets'),
]
