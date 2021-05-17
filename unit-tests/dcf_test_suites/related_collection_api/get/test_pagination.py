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

    def test_list(self):
        resp = self.superuser_client.get("/brand/1/products")
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
            {"id": 2, "barcode": "product_2", "brand_id": 1},
        )

    def test_list_next_page(self):
        resp = self.superuser_client.get("/brand/1/products?_page=2")
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 2, "limit": 50, "total": 100},
            data,
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 50)
        self.assertDictContainsSubset(
            objects[0], {"id": 51, "barcode": "product_51", "brand_id": 1}
        )
        self.assertDictContainsSubset(
            objects[1],
            {"id": 52, "barcode": "product_52", "brand_id": 1},
        )

    def test_page_with_limit(self):
        resp = self.superuser_client.get("/brand/1/products?_page=3&_limit=30")
        data = resp.json()
        self.assertDictContainsSubset({"page": 3, "limit": 30, "total": 100}, data)
        objects = data["objects"]
        self.assertEqual(len(objects), 30)
        self.assertDictEqual(
            {"id": 61, "barcode": "product_61", "brand_id": 1}, objects[0]
        )

    def test_limit_without_page(self):
        resp = self.superuser_client.get("/brand/2/products?_limit=5")
        data = resp.json()
        self.assertDictContainsSubset({"page": 1, "limit": 5, "total": 50}, data)
        objects = data["objects"]
        self.assertDictEqual(
            {"id": 101, "barcode": "product_101", "brand_id": 2}, objects[0]
        )

    def test_extend_past_page(self):
        resp = self.superuser_client.get("/brand/2/products?_page=2")
        data = resp.json()
        self.assertDictEqual({"detail": "Invalid page."}, data)

    def test_extend_past_page_with_limit(self):
        resp = self.superuser_client.get("/brand/2/products?_limit=20&_page=4")
        data = resp.json()
        self.assertDictEqual({"detail": "Invalid page."}, data)

    def test_key_single_empty(self):
        resp = self.superuser_client.get("/brand/2/products?barcode=product_100")
        data = resp.json()
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 0}, data)
        objects = data["objects"]
        self.assertEqual(len(objects), 0)

    def test_key_single_filled(self):
        resp = self.superuser_client.get("/brand/1/products?barcode=product_60")
        data = resp.json()
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 1}, data)
        objects = data["objects"]
        self.assertEqual(len(objects), 1)
        self.assertDictEqual(
            {"id": 60, "barcode": "product_60", "brand_id": 1}, objects[0]
        )

    def test_key_multiple_filled(self):
        resp = self.superuser_client.get(
            "/brand/2/products?barcode=product_102&brand_id=2"
        )
        data = resp.json()
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 1}, data)
        objects = data["objects"]
        self.assertEqual(len(objects), 1)
        self.assertDictEqual(
            {"id": 102, "barcode": "product_102", "brand_id": 2}, objects[0]
        )

    def test_key_multiple_empty(self):
        resp = self.superuser_client.get(
            "/brand/2/products?barcode=product_102&brand_id=1"
        )
        data = resp.json()
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 0}, data)
        objects = data["objects"]
        self.assertEqual(len(objects), 0)

    def test_key_array_filled(self):
        resp = self.superuser_client.get(
            "/brand/1/products?barcode__in[]=product_10&barcode__in[]=product_11"
        )
        data = resp.json()
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 2}, data)
        objects = data["objects"]
        self.assertEqual(len(objects), 2)
        self.assertDictEqual(
            objects[0], {"id": 10, "barcode": "product_10", "brand_id": 1}
        )

    def test_key_array_empty(self):
        resp = self.superuser_client.get(
            "/brand/1/products?barcode__in[]=product_101&barcode__in[]=product_111"
        )
        data = resp.json()
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 0}, data)
        objects = data["objects"]
        self.assertEqual(len(objects), 0)

    def test_order_positive(self):
        resp = self.superuser_client.get("/brand/1/products?_order_by=barcode")
        data = resp.json()
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 100}, data)
        objects = data["objects"]
        self.assertDictEqual(
            objects[0], {"id": 1, "barcode": "product_1", "brand_id": 1}
        )
        self.assertDictEqual(
            objects[1], {"id": 10, "barcode": "product_10", "brand_id": 1}
        )
        self.assertDictEqual(
            objects[2], {"id": 100, "barcode": "product_100", "brand_id": 1}
        )

    def test_order_negative(self):
        resp = self.superuser_client.get("/brand/1/products?_order_by=-barcode")
        data = resp.json()
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 100}, data)
        objects = data["objects"]
        self.assertDictEqual(
            objects[0], {"id": 99, "barcode": "product_99", "brand_id": 1}
        )
        self.assertDictEqual(
            objects[1], {"id": 98, "barcode": "product_98", "brand_id": 1}
        )
        self.assertDictEqual(
            objects[2], {"id": 97, "barcode": "product_97", "brand_id": 1}
        )

    def test_order_page(self):
        resp = self.superuser_client.get("/brand/1/products?_order_by=barcode&_page=2")
        data = resp.json()
        self.assertDictContainsSubset({"page": 2, "limit": 50, "total": 100}, data)
        objects = data["objects"]
        self.assertDictEqual(
            objects[0], {"id": 54, "barcode": "product_54", "brand_id": 1}
        )
        self.assertDictEqual(
            objects[1], {"id": 55, "barcode": "product_55", "brand_id": 1}
        )
        self.assertDictEqual(
            objects[2], {"id": 56, "barcode": "product_56", "brand_id": 1}
        )

    # error: multiple keys not working
    def test_order_multiple_keys(self):
        resp = self.superuser_client.get("/brand/1/products?_order_by=barcode,brand")
        data = resp.json()
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 100}, data)
        objects = data["objects"]
        self.assertDictEqual(
            objects[0], {"id": 1, "barcode": "product_1", "brand_id": 1}
        )
        self.assertDictEqual(
            objects[1], {"id": 10, "barcode": "product_10", "brand_id": 1}
        )
        self.assertDictEqual(
            objects[2], {"id": 100, "barcode": "product_100", "brand_id": 1}
        )
