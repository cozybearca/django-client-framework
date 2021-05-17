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
        self.products = [
            Product.objects.create(barcode=f"product_{i+1}", brand=self.brand)
            for i in range(100)
        ]

    def test_patch_success(self):
        self.superuser_client.patch(
            "/product/1/brand", data=[2], content_type="application/json"
        )
        self.assertEqual(2, Product.objects.get(id=1).brand_id)

    def test_patch_failed_invalid_fk(self):
        resp = self.superuser_client.patch(
            "/product/1/brand", data=[23], content_type="application/json"
        )
        data = resp.json()
        self.assertDictEqual(
            data, {"brand_id": 'Invalid pk "23" - object does not exist.'}
        )

    def test_patch_failed_multiple_ids(self):
        resp = self.superuser_client.patch(
            "/product/1/brand", data=[23, 24], content_type="application/json"
        )
        data = resp.json()
        self.assertDictEqual(data, {"input_error": "You must input exactly one id"})
