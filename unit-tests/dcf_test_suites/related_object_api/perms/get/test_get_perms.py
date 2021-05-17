from django.test import TestCase
from rest_framework.test import APIClient
from django_client_framework import permissions as p
from dcf_test_app.models import Product
from dcf_test_app.models import Brand
from django.contrib.auth.models import User


class TestGetPerms(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.br1 = Brand.objects.create(name="br1")
        self.br2 = Brand.objects.create(name="br2")
        self.pr1 = Product.objects.create(barcode="pr1", brand=self.br1)
        self.pr2 = Product.objects.create(barcode="pr2", brand=self.br2)
        p.clear_permissions()

    def test_get_no_permissions(self):
        resp = self.user_client.get("/product/1/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_incorrect_parent_permission(self):
        p.set_perms_shortcut(self.user, Product, "wcd", field_name="brand")
        resp = self.user_client.get("/product/1/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_parent_permission_correct(self):
        p.set_perms_shortcut(self.user, Product, "r")
        resp = self.user_client.get("/product/1/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_parent_permission_correct_ver_2(self):
        p.set_perms_shortcut(self.user, Product, "r", field_name="brand")
        resp = self.user_client.get("/product/1/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_parent_permission_incorrect_reverse_perm(self):
        p.set_perms_shortcut(self.user, Product, "r", field_name="brand")
        p.set_perms_shortcut(self.user, Brand, "wcd")
        resp = self.user_client.get("/product/1/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_parent_permission_incorrect_reverse_perm_ver_2(self):
        p.set_perms_shortcut(self.user, Product, "r")
        p.set_perms_shortcut(self.user, Brand, "wcd", field_name="name")
        resp = self.user_client.get("/product/1/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_parent_permission_incorrect_reverse_perm_ver_3(self):
        p.set_perms_shortcut(self.user, Product.objects.get(id=1), "r")
        p.set_perms_shortcut(self.user, Brand.objects.get(id=2), "r")
        resp = self.user_client.get("/product/1/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_parent_permission_incorrect_reverse_perm_ver_4(self):
        p.set_perms_shortcut(self.user, Product.objects.get(id=1), "r")
        p.set_perms_shortcut(self.user, Brand.objects.get(id=1), "r", field_name="name")
        resp = self.user_client.get("/product/1/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_parent_permission_correct_reverse_perm(self):
        p.set_perms_shortcut(self.user, Product, "r", field_name="brand")
        p.set_perms_shortcut(self.user, Brand, "r")
        resp = self.user_client.get("/product/1/brand")
        data = resp.json()
        self.assertDictEqual({"id": 1, "name": "br1"}, data)

    def test_get_only_parent_permission_correct_reverse_perm_ver_2(self):
        p.set_perms_shortcut(self.user, Product, "r")
        p.set_perms_shortcut(self.user, Brand, "r")
        resp = self.user_client.get("/product/1/brand")
        data = resp.json()
        self.assertDictEqual({"id": 1, "name": "br1"}, data)

    def test_get_only_parent_permission_correct_reverse_perm_ver_3(self):
        p.set_perms_shortcut(
            self.user, Product.objects.get(id=1), "r", field_name="brand"
        )
        p.set_perms_shortcut(self.user, Brand.objects.get(id=1), "r")
        resp = self.user_client.get("/product/1/brand")
        data = resp.json()
        self.assertDictEqual({"id": 1, "name": "br1"}, data)

    def test_get_only_parent_permission_correct_reverse_perm_ver_4(self):
        p.set_perms_shortcut(self.user, Product.objects.get(id=1), "r")
        p.set_perms_shortcut(self.user, Brand.objects.get(id=1), "r")
        resp = self.user_client.get("/product/1/brand")
        data = resp.json()
        self.assertDictEqual({"id": 1, "name": "br1"}, data)
