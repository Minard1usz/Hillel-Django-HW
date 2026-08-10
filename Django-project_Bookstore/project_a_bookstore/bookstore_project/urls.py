from django.contrib import admin
from django.views.generic import RedirectView
from django.urls import path, include, re_path
from shop_app.views import store, health_check
from django.conf import settings
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from django.views.static import serve
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
api_router.register(r"categories", CategoryViewSet, basename="category")
api_router.register(r"books", BookViewSet, basename="book")
api_router.register(r"cart", CartViewSet, basename="cart")
api_router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_router.urls)),
    path("", RedirectView.as_view(url="shop/", permanent=True)),
    path("i18n/", include("django.conf.urls.i18n")),
    path("shop/", include("shop_app.urls")),
    path("users/", include("users.urls")),
    path("orders/", include("orders.urls", namespace="orders")),
    # Єдиний ендпоінт для всього REST API
    path("api/v1/", include(api_router.urls)),
    # JWT Авторизація
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # Документація
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns

else:
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]

