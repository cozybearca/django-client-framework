from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from dcf_test_app.models import Product
from dcf_test_app.models import Brand


class TestDelete(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(username="testuser")
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(self.superuser)
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

    def test_delete_objects_success(self):
        resp = self.superuser_client.delete(
            "/brand/1/products", data=[1, 2, 3], content_type="application/json"
        )
        self.assertEquals(50, len(resp.json()["objects"]))
        self.assertTrue(Product.objects.get(id=1).brand_id is None)
        self.assertTrue(Product.objects.get(id=2).brand_id is None)
        self.assertTrue(Product.objects.get(id=3).brand_id is None)
        self.assertTrue(Product.objects.filter(brand_id=1).count() == 97)

    def test_delete_objects_none(self):
        resp = self.superuser_client.delete(
            "/brand/1/products", data=[101, 102], content_type="application/json"
        )
        self.assertEquals(50, len(resp.json()["objects"]))
        self.assertTrue(Product.objects.get(id=101).brand_id == 2)
        self.assertTrue(Product.objects.get(id=102).brand_id == 2)
        self.assertTrue(Product.objects.filter(brand_id=1).count() == 100)
