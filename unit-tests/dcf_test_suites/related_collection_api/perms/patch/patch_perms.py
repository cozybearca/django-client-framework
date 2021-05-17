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


    def test_patch_no_permissions(self):
        resp = self.user_client.patch("/brand/1/products", data=[3], content_type="application/json")
        self.assertEquals(404, resp.status_code)

    
    def test_patch_incorrect_parent_permissions(self):
        p.set_perms_shortcut(self.user, Brand, "r", field_name="products")
        resp = self.user_client.patch("/brand/1/products", data=[3], content_type="application/json")
        self.assertEquals(404, resp.status_code)

    
    def test_patch_correct_parent_perms(self):
        p.set_perms_shortcut(self.user, Brand, "w", field_name="products")
        resp = self.user_client.patch("/brand/1/products", data=[3], content_type="application/json")
        self.assertEquals(404, resp.status_code)


    def test_patch_correct_parent_incorrect_reverse_field_perms(self):
        p.set_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.set_perms_shortcut(self.user, Product, "r", field_name="brand")
        resp = self.user_client.patch("/brand/1/products", data=[3], content_type="application/json")
        self.assertEquals(404, resp.status_code)


    def test_patch_correct_parent_incorrect_reverse_field_perms_ver_2(self):
        p.set_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.set_perms_shortcut(self.user, Product, "r")
        resp = self.user_client.patch("/brand/1/products", data=[3], content_type="application/json")
        self.assertEquals(403, resp.status_code)


    def test_patch_correct_parent_and_reverse_perms(self):
        p.set_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.set_perms_shortcut(self.user, Product, "w")
        resp = self.user_client.patch("/brand/1/products", data=[3], content_type="application/json")
        data = resp.json()
        self.assertEquals(True, data["success"])
        self.assertEquals(1, Product.objects.get(id=3).brand_id)
        self.assertEquals(1, Product.objects.filter(brand_id=1).count())


    def test_patch_correct_parent_and_reverse_perms_ver_2(self):
        p.set_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.set_perms_shortcut(self.user, Product, "w", field_name="brand")
        resp = self.user_client.patch("/brand/1/products", data=[3], content_type="application/json")
        data = resp.json()
        self.assertEquals(True, data["success"])
        self.assertEquals(1, Product.objects.get(id=3).brand_id)
        self.assertEquals(1, Product.objects.filter(brand_id=1).count())

    
    def test_patch_correct_parent_and_reverse_perms_but_can_only_read_parent(self):
        p.set_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.set_perms_shortcut(self.user, Brand, "r")
        p.set_perms_shortcut(self.user, Product, "w", field_name="brand")
        resp = self.user_client.patch("/brand/1/products", data=[3], content_type="application/json")
        data = resp.json()
        self.assertEquals(1, Product.objects.filter(brand_id=1).count())
        self.assertEquals(0, len(data["objects"]))


    def test_patch_correct_parent_and_reverse_perms_with_correct_read_perms(self):
        p.set_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.set_perms_shortcut(self.user, Brand, "r")
        p.set_perms_shortcut(self.user, Product, "r")
        p.set_perms_shortcut(self.user, Product, "w", field_name="brand")
        resp = self.user_client.patch("/brand/1/products", data=[101, 102, 103], content_type="application/json")
        data = resp.json()
        self.assertEquals(3, Product.objects.filter(brand_id=1).count())
        self.assertEquals(3, len(data["objects"]))
        self.assertDictEqual( {"id": 101, "barcode": "product_101", "brand_id": 1}, data["objects"][0])


    def test_patch_correct_parent_and_reverse_perms_with_correct_read_perms_ver2(self):
        p.set_perms_shortcut(self.user, Brand, "wr", field_name="products")
        p.set_perms_shortcut(self.user, Product.objects.get(id=101), "r")
        p.set_perms_shortcut(self.user, Product.objects.get(id=102), "r")
        p.set_perms_shortcut(self.user, Product, "w", field_name="brand")
        resp = self.user_client.patch("/brand/1/products", data=[101, 102, 103], content_type="application/json")
        data = resp.json()
        self.assertEquals(3, Product.objects.filter(brand_id=1).count())
        self.assertEquals(2, len(data["objects"]))
        self.assertDictEqual( {"id": 101, "barcode": "product_101", "brand_id": 1}, data["objects"][0])