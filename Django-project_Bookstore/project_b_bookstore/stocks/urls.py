from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StockViewSet, ReserveStockView, ReleaseStockView

router = DefaultRouter()
router.register(r"stocks", StockViewSet, basename="stock")

urlpatterns = [
    path("", include(router.urls)),
    path("reserve/", ReserveStockView.as_view(), name="reserve-stock"),
    path("release/", ReleaseStockView.as_view(), name="release-stock"),
]
