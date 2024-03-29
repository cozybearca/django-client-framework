from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from dcf_test_app.models import Product
from dcf_test_app.models import Brand
from django_client_framework import permissions as p


class TestPaginationPerms(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.brand = Brand.objects.create(name="brand")
        self.products = [
            Product.objects.create(barcode=f"product_{i+1}", brand=self.brand)
            for i in range(100)
        ]
        self.br2 = Brand.objects.create(name="nike")
        self.new_products = [
            Product.objects.create(barcode=f"product_{i+101}", brand=self.br2)
            for i in range(50)
        ]

    def test_post_no_permissions(self):
        resp = self.user_client.post(
            "/brand/1/products", data=[101], content_type="application/json"
        )
        self.assertEquals(404, resp.status_code)

    def test_post_incorrect_parent_permissions(self):
        p.set_perms_shortcut(self.user, Brand, "r", field_name="products")
        resp = self.user_client.post(
            "/brand/1/products", data=[101], content_type="application/json"
        )
        self.assertEquals(404, resp.status_code)

    def test_post_correct_parent_perms(self):
        p.set_perms_shortcut(self.user, Brand, "w", field_name="products")
        resp = self.user_client.post(
            "/brand/1/products", data=[101], content_type="application/json"
        )
        self.assertEquals(404, resp.status_code)

    def test_post_correct_parent_incorrect_reverse_field_perms(self):
        p.set_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.set_perms_shortcut(self.user, Product, "r", field_name="brand")
        resp = self.user_client.post(
            "/brand/1/products", data=[101], content_type="application/json"
        )
        self.assertEquals(404, resp.status_code)

    def test_post_correct_parent_incorrect_reverse_field_perms_ver_2(self):
        p.set_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.set_perms_shortcut(self.user, Product, "r")
        resp = self.user_client.post(
            "/brand/1/products", data=[101], content_type="application/json"
        )
        self.assertEquals(403, resp.status_code)

    def test_post_correct_parent_and_reverse_perms(self):
        p.set_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.set_perms_shortcut(self.user, Product, "w")
        resp = self.user_client.post(
            "/brand/1/products", data=[101], content_type="application/json"
        )
        data = resp.json()
        self.assertDictEqual({"success": True}, data)
        self.assertEquals(1, Product.objects.get(id=101).brand_id)

    def test_post_correct_parent_and_reverse_perms_ver_2(self):
        p.set_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.set_perms_shortcut(self.user, Product, "w", field_name="brand")
        p.set_perms_shortcut(self.user, Product, "r")
        resp = self.user_client.post(
            "/brand/1/products", data=[101], content_type="application/json"
        )
        data = resp.json()
        self.assertDictEqual({"success": True}, data)
        self.assertEquals(1, Product.objects.get(id=101).brand_id)

    def test_post_correct_parent_and_reverse_perms_but_can_only_read_parent(self):
        p.set_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.set_perms_shortcut(self.user, Brand, "r")
        p.set_perms_shortcut(self.user, Product, "w", field_name="brand")
        resp = self.user_client.post(
            "/brand/1/products", data=[101], content_type="application/json"
        )
        data = resp.json()
        self.assertEquals(1, Product.objects.get(id=101).brand_id)
        self.assertEquals(0, len(data["objects"]))

    def test_post_correct_parent_and_reverse_perms_with_correct_read_perms(self):
        p.set_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.set_perms_shortcut(self.user, Brand, "r")
        p.set_perms_shortcut(self.user, Product, "r")
        p.set_perms_shortcut(self.user, Product, "w", field_name="brand")
        resp = self.user_client.post(
            "/brand/1/products", data=[101], content_type="application/json"
        )
        data = resp.json()
        self.assertEquals(50, len(data["objects"]))
        self.assertDictEqual(
            data["objects"][0], {"id": 1, "barcode": "product_1", "brand_id": 1}
        )
        self.assertEquals(1, Product.objects.get(id=101).brand_id)

    def test_post_correct_parent_and_reverse_perms_with_correct_read_perms_v2(self):
        p.set_perms_shortcut(
            self.user, Brand.objects.get(id=1), "wr", field_name="products"
        )
        p.set_perms_shortcut(self.user, Product.objects.filter(id=10), "r")
        p.set_perms_shortcut(self.user, Product.objects.filter(id=9), "r")
        p.set_perms_shortcut(self.user, Product.objects.filter(id=11), "r")
        p.set_perms_shortcut(
            self.user, Product.objects.filter(id=101), "w", field_name="brand"
        )
        resp = self.user_client.post(
            "/brand/1/products", data=[101], content_type="application/json"
        )
        data = resp.json()
        self.assertEquals(3, len(data["objects"]))
        self.assertDictEqual(
            data["objects"][0], {"id": 9, "barcode": "product_9", "brand_id": 1}
        )
        self.assertEquals(101, Product.objects.filter(brand_id=1).count())
        self.assertEquals(1, Product.objects.get(id=101).brand_id)
