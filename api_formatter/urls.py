from django.conf.urls import url, include
from rest_framework.schemas import get_schema_view
from .routers import RACRouter

from .views import AgentViewSet, CollectionViewSet, ObjectViewSet, TermViewSet, SearchView

router = RACRouter()
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
    url(r'search/', SearchView.as_view({'get': 'list'}), name='search'),
    url(r'^schema/', schema_view, name='schema'),
]
