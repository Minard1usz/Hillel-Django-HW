from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Кастомний дозвіллєвий клас:

    дозволяє перегляд/редагування об'єкта тільки його власнику (за email або
    зв'язком з user).
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Адмін має повний доступ
        if request.user.is_staff:
            return True

        # Користувач бачить замовлення тільки якщо email збігається
        return obj.email == request.user.email
