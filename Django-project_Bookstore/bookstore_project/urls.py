from django.contrib import admin
from django.views.generic import RedirectView
from django.urls import path, include
from shop_app.views import store
from django.conf import settings
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Імпорт ViewSets
from shop_app.api_views import BookViewSet, CategoryViewSet
from orders.api_views import CartViewSet, OrderViewSet

# Створення єдиного головного роутеру для цілого проєкту
api_router = DefaultRouter()
api_router.register(r'categories', CategoryViewSet, basename='category')
api_router.register(r'books', BookViewSet, basename='book')
api_router.register(r'cart', CartViewSet, basename='cart')
api_router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='shop/', permanent=True)),
    path('i18n/', include('django.conf.urls.i18n')),
    path('shop/', include('shop_app.urls')),
    path('users/', include('users.urls')),
    path('orders/', include('orders.urls', namespace='orders')),

    # Єдиний ендпоінт для всього REST API
    path('api/v1/', include(api_router.urls)),

    # JWT Авторизація
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Документація
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns