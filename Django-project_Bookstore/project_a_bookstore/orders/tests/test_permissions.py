from types import SimpleNamespace
from unittest.mock import Mock
from django.test import TestCase
from orders.permissions import IsOwner


class IsOwnerPermissionTest(TestCase):

    def setUp(self):
        self.permission = IsOwner()
        self.view = Mock()

    def test_has_object_permission_anonymous_user(self):
        """Анонімний користувач (або user=None) НЕ має доступу"""
        request = SimpleNamespace(user=None)
        obj = SimpleNamespace(email="owner@example.com")

        self.assertFalse(self.permission.has_object_permission(request, self.view, obj))

    def test_has_object_permission_not_authenticated_user(self):
        """Неавторизований користувач (is_authenticated=False) НЕ має доступу"""
        request = SimpleNamespace(user=SimpleNamespace(is_authenticated=False))
        obj = SimpleNamespace(email="owner@example.com")

        self.assertFalse(self.permission.has_object_permission(request, self.view, obj))

    def test_has_object_permission_staff_user(self):
        """Адміністратор має доступ до будь-якого замовлення"""
        request = SimpleNamespace(
            user=SimpleNamespace(
                is_authenticated=True, is_staff=True, email="admin@example.com"
            )
        )
        obj = SimpleNamespace(email="client@example.com")

        self.assertTrue(self.permission.has_object_permission(request, self.view, obj))

    def test_has_object_permission_owner_user(self):
        """Власник об'єкта має доступ"""
        request = SimpleNamespace(
            user=SimpleNamespace(
                is_authenticated=True, is_staff=False, email="owner@example.com"
            )
        )
        obj = SimpleNamespace(email="owner@example.com")

        self.assertTrue(self.permission.has_object_permission(request, self.view, obj))

    def test_has_object_permission_other_user(self):
        """Сторонній користувач НЕ має доступу"""
        request = SimpleNamespace(
            user=SimpleNamespace(
                is_authenticated=True, is_staff=False, email="stranger@example.com"
            )
        )
        obj = SimpleNamespace(email="owner@example.com")

        self.assertFalse(self.permission.has_object_permission(request, self.view, obj))
