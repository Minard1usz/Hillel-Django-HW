from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Кастомний дозвіллєвий клас: дозволяє перегляд/редагування об'єкта
    тільки його власнику (за email або зв'язком з user).
    """

    def has_object_permission(self, request, view, obj):
        # Адмін має повний доступ до замовлення
        if request.user and request.user.is_staff:
            return True

        # Користувач бачить замовлення тільки, якщо зберігається email
        return obj.mail == request.user.email
