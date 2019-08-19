from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from .views import AgentViewSet

router = DefaultRouter()
router.register(r'agents', AgentViewSet, basename='agent')

urlpatterns = [
    url(r'^', include(router.urls)),
]
