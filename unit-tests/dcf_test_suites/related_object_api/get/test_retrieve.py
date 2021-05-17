from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from dcf_test_app.models import Product
from dcf_test_app.models import Brand


class TestRetrieve(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(username="testuser")
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(self.superuser)
        self.brand = Brand.objects.create(name="brand")
        self.product = Product.objects.create(barcode="product", brand=self.brand)
        self.br2 = Brand.objects.create(name="nike")

    def test_get(self):
        resp = self.superuser_client.get("/product/1/brand")
        data = resp.json()
        self.assertDictEqual(data, {"id": 1, "name": "brand"})
    
    def test_get_failed(self):
        resp = self.superuser_client.get("/product/2/brand")
        self.assertEqual(resp.status_code, 404)