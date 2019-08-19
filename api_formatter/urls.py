from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from .views import AgentViewSet, TermViewSet

router = DefaultRouter()
router.register(r'agents', AgentViewSet, basename='agent')
router.register(r'terms', TermViewSet, basename='term')

urlpatterns = [
    url(r'^', include(router.urls)),
]
