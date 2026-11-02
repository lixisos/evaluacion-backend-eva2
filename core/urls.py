from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from app.views import (
    index_view, login_view, logout_view,
    HerramientaViewSet, ContratistaViewSet,
    PrestamoViewSet, MantenimientoViewSet
)

router = DefaultRouter()
router.register(r'herramientas', HerramientaViewSet, basename='herramientas')
router.register(r'contratistas', ContratistaViewSet, basename='contratistas')
router.register(r'prestamos', PrestamoViewSet, basename='prestamos')
router.register(r'mantenimientos', MantenimientoViewSet, basename='mantenimientos')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]