from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from dcf_test_app.models import Product
from dcf_test_app.models import Brand
from django.forms.models import model_to_dict
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
            Product.objects.create(barcode=f"product_{i+101}", brand=self.br2 )
            for i in range(50)
        ]


    def test_no_permissions_get(self):
        resp = self.user_client.get("/brand/1/products")
        self.assertEquals(404, resp.status_code)


    # error: needs to only show the "products" that have read-level permission, right now shows all
    def test_only_parent_permissions_get(self):
        p.set_perms_shortcut(self.user, Brand, "r", field_name="products")
        resp = self.user_client.get("/brand/1/products")
        data = resp.json()
        objects = data["objects"]
        self.assertEquals(len(objects), 0)


    # error: need to only show product_3
    def test_only_parent_permissions_get(self):
        p.set_perms_shortcut(self.user, Brand, "r", field_name="products")
        p.set_perms_shortcut(self.user, self.products[2], "r")
        resp = self.user_client.get("/brand/1/products")
        data = resp.json()
        objects = data["objects"]
        self.assertEquals(len(objects), 1)
        self.assertDictEqual({"id": 3, "barcode": "product_3", "brand_id": 1}, objects[0])


    # error: need to return no objects
    def test_correct_parent_incorrect_reverse_perms_get(self):
        p.set_perms_shortcut(self.user, Brand, "r", field_name="products")
        p.set_perms_shortcut(self.user, Product, "wcd")
        resp = self.user_client.get("/brand/1/products")
        data = resp.json()
        self.assertEquals(0, data["total"])
        self.assertEquals(len(data["objects"]), 0)

    
    def test_get_with_object_level_perm(self):
        p.set_perms_shortcut(self.user, Brand, "r", field_name="products")
        p.set_perms_shortcut(self.user, Product, "r")
        resp = self.user_client.get("/brand/1/products")
        data = resp.json()
        objects = data["objects"]
        self.assertEquals(50, len(objects))
        self.assertDictEqual(objects[0], {"id": 1, "barcode": "product_1", "brand_id": 1})
        self.assertDictEqual(objects[49], {"id": 50, "barcode": "product_50", "brand_id": 1})