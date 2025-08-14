
from rest_framework.routers import DefaultRouter

from api.views import KndViewSet, SimpleFileUploadView
from django.urls import include, path


router_api_v1 = DefaultRouter()
router_api_v1.register('knd', KndViewSet, basename='knd-v1')

v1_patterns = [
    path('', include(router_api_v1.urls)),
    path('upload/', SimpleFileUploadView.as_view(), name='file-upload'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]

urlpatterns = [
    path('v1/', include(v1_patterns)),
]
