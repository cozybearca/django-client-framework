from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from dcf_test_app.models import Product
from dcf_test_app.models import Brand
from django.forms.models import model_to_dict


class TestPost(TestCase):
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


    def test_post_related_success(self):
        resp = self.superuser_client.post("/brand/1/products", data=[101, 102], content_type='application/json')
        self.assertEquals(50, len(resp.json()["objects"]))
        self.assertEqual(Product.objects.get(barcode="product_101").brand_id, 1)
        self.assertEqual(Product.objects.get(barcode="product_102").brand_id, 1)
        self.assertEqual(Product.objects.filter(brand_id=1).count(), 102)
    

    def test_post_related_failure(self):
        resp = self.superuser_client.post("/brand/1/products", data=[160, 170], content_type='application/json')
        self.assertEquals(50, len(resp.json()["objects"]))
        self.assertEqual(Product.objects.filter(brand_id=1).count(), 100)


    def test_post_related_partial_failure(self):
        resp = self.superuser_client.post("/brand/1/products", data=[103, 180], content_type='application/json')
        self.assertEquals(50, len(resp.json()["objects"]))
        self.assertEqual(Product.objects.filter(brand_id=1).count(), 101)
        self.assertEqual(Product.objects.get(barcode="product_103").brand_id, 1)