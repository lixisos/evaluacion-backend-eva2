"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from app.views import (MaquinariaViewSet, MiCarroView, ItemCarroViewSet, CheckoutView, ContratoViewSet, CustomTokenObtainPairView)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from app.views import login_view, catalogo_view, carro_view, dashboard_view
from app.views import registro_cliente, registro_view

router = DefaultRouter()
router.register(r'maquinarias', MaquinariaViewSet, basename='maquinaria')
router.register(r'carro-items', ItemCarroViewSet, basename='carro-item')
router.register(r'contratos', ContratoViewSet, basename='contrato')


urlpatterns = [
    path('admin/', admin.site.urls),
    # Autenticación JWT
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Endpoints de la lógica de negocio
    path('api/', include(router.urls)),
    path('api/mi-carro/', MiCarroView.as_view(), name='mi-carro'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('login/', login_view, name='login'),
    path('', catalogo_view, name='catalogo'),
    path('carro/', carro_view, name='carro'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('registro/', registro_view, name='registro-view'),
    path('api/registro/', registro_cliente, name='api-registro'),
]
    

