from django.test import TestCase
from rest_framework.test import APIClient
from django_client_framework import permissions as p
from dcf_test_app.models import Product
from dcf_test_app.models import Brand
from django.contrib.auth.models import User


class TestPatchPerms(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.br1 = Brand.objects.create(name="br1")
        self.br2 = Brand.objects.create(name="br2")
        self.pr1 = Product.objects.create(barcode="pr1", brand=self.br1)
        self.pr2 = Product.objects.create(barcode="pr2", brand=self.br2)
        p.clear_permissions()

    def test_patch_no_permission(self):
        resp = self.user_client.patch(
            "/product/1/brand", data=[2], content_type="application/json"
        )
        self.assertEqual(404, resp.status_code)

    def test_patch_incorrect_permission(self):
        p.set_perms_shortcut(self.user, Product, "rcd")
        resp = self.user_client.patch(
            "/product/1/brand", data=[2], content_type="application/json"
        )
        self.assertEqual(403, resp.status_code)

    def test_patch_only_parent_permission(self):
        p.set_perms_shortcut(self.user, Product, "w")
        resp = self.user_client.patch(
            "/product/1/brand", data=[2], content_type="application/json"
        )
        self.assertEqual(404, resp.status_code)

    def test_patch_parent_but_incorrect_related_perms(self):
        p.set_perms_shortcut(self.user, Product, "w")
        p.set_perms_shortcut(self.user, Brand, "rcd")
        resp = self.user_client.patch(
            "/product/1/brand", data=[2], content_type="application/json"
        )
        self.assertEqual(403, resp.status_code)

    def test_correct_patch_perms_no_read(self):
        p.set_perms_shortcut(self.user, Product, "w")
        p.set_perms_shortcut(self.user, Brand, "w")
        resp = self.user_client.patch(
            "/product/1/brand", data=[2], content_type="application/json"
        )
        self.assertEqual(2, Product.objects.get(id=1).brand_id)
        self.assertDictEqual({"success": True}, resp.json())

    def test_correct_patch_perms_no_read_v2(self):
        p.set_perms_shortcut(self.user, Product, "w")
        p.set_perms_shortcut(self.user, Brand, "wr")
        resp = self.user_client.patch(
            "/product/1/brand", data=[2], content_type="application/json"
        )
        self.assertEqual(2, Product.objects.get(id=1).brand_id)
        self.assertDictEqual({"success": True}, resp.json())

    def test_correct_patch_perms_can_read(self):
        p.set_perms_shortcut(self.user, Brand, "rw")
        p.set_perms_shortcut(self.user, Product, "rw")
        resp = self.user_client.patch(
            "/product/1/brand", data=[2], content_type="application/json"
        )
        self.assertEqual(2, Product.objects.get(id=1).brand_id)
        self.assertDictEqual({"id": 2, "name": "br2"}, resp.json())

    def test_correct_patch_perms_can_read_v2(self):
        p.set_perms_shortcut(self.user, Product.objects.get(id=1), "rw")
        p.set_perms_shortcut(self.user, Brand.objects.get(id=1), "w")
        p.set_perms_shortcut(self.user, Brand.objects.get(id=2), "rw")
        resp = self.user_client.patch(
            "/product/1/brand", data=[2], content_type="application/json"
        )
        self.assertEqual(2, Product.objects.get(id=1).brand_id)
        self.assertDictEqual({"id": 2, "name": "br2"}, resp.json())

    def test_correct_patch_perms_can_read_v3(self):
        p.set_perms_shortcut(
            self.user, Product.objects.get(id=1), "rw", field_name="brand"
        )
        p.set_perms_shortcut(
            self.user, Brand.objects.get(id=1), "w", field_name="products"
        )
        p.set_perms_shortcut(self.user, Brand.objects.get(id=2), "r")
        p.set_perms_shortcut(
            self.user, Brand.objects.get(id=2), "w", field_name="products"
        )
        resp = self.user_client.patch(
            "/product/1/brand", data=[2], content_type="application/json"
        )
        self.assertEqual(2, Product.objects.get(id=1).brand_id)
        self.assertDictEqual({"id": 2, "name": "br2"}, resp.json())
