
from rest_framework.routers import DefaultRouter

from api.views import KndViewSet
from django.urls import include, path


router_api_v1 = DefaultRouter()
router_api_v1.register(r'knd', KndViewSet, basename='knd-v1')
router_api_v1.register(r'knd/upload_qrcod', KndViewSet, basename='knd-qrcodes-upload')

v1_patterns = [
    path('', include(router_api_v1.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]

urlpatterns = [
    path('v1/', include(v1_patterns)),
]
