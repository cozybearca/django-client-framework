from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from dcf_test_app.models import Product
from dcf_test_app.models import Brand


class TestPagination(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(username="testuser")
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(self.superuser)
        self.brands = [Brand.objects.create(name=f"name_{i+1}") for i in range(100)]
        self.products = [
            Product.objects.create(
                barcode=f"product_{i+1}", brand=self.brands[i] if i % 2 == 0 else None
            )
            for i in range(100)
        ]

    def test_list(self):
        resp = self.superuser_client.get("/product")
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "total": 100},
            data,
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 50)
        self.assertDictContainsSubset(
            objects[0], {"id": 1, "barcode": "product_1", "brand_id": 1}
        )
        self.assertDictContainsSubset(
            objects[1],
            {"id": 2, "barcode": "product_2", "brand_id": None},
        )

    def test_list_next_page(self):
        resp = self.superuser_client.get("/product?_page=2")
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 2, "limit": 50, "total": 100},
            data,
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 50)
        self.assertDictContainsSubset(
            objects[0], {"id": 51, "barcode": "product_51", "brand_id": 51}
        )
        self.assertDictContainsSubset(
            objects[1],
            {"id": 52, "barcode": "product_52", "brand_id": None},
        )
