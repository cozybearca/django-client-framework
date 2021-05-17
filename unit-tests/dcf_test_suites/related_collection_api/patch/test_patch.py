from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from dcf_test_app.models import Product
from dcf_test_app.models import Brand
from django.forms.models import model_to_dict


class TestPatch(TestCase):
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
            Product.objects.create(barcode=f"product_{i+101}", brand=self.br2 )
            for i in range(50)
        ]

    
    def test_patch_objects_all(self):
        resp = self.superuser_client.patch("/brand/1/products", data=[1, 2], content_type='application/json')
        self.assertEqual(Product.objects.filter(brand_id=1).count(), 2)
        self.assertEqual(Product.objects.get(id=1).brand_id, 1)
        self.assertEqual(Product.objects.get(id=2).brand_id, 1)
        self.assertTrue(Product.objects.get(id=3).brand_id!=1)


    def test_patch_objects_unlink_all(self):
        resp = self.superuser_client.patch("/brand/1/products", data=[], content_type='application/json')
        self.assertEquals(0, len(resp.json()["objects"]))
        self.assertEqual(Product.objects.filter(brand_id=1).count(), 0)
        self.assertEqual(Product.objects.get(id=1).brand_id, None)
        self.assertEqual(Product.objects.get(id=2).brand_id, None)

    
    def test_patch_objects_invalid_key(self):
        resp = self.superuser_client.patch("/brand/1/products", data=[200], content_type='application/json')
        self.assertEquals(len(resp.json()["objects"]), 0)
        self.assertEquals(0, Product.objects.filter(brand_id=1).count())