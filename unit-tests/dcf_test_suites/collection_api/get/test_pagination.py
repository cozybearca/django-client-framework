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
        Product.objects.create(barcode="product_99", brand=None)

    def test_list(self):
        resp = self.superuser_client.get("/product")
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "total": 101},
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
            {"page": 2, "limit": 50, "total": 101},
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

    def test_page_with_limit(self):
        resp = self.superuser_client.get("/product?_page=3&_limit=10")
        data = resp.json()
        objects = data["objects"]
        self.assertDictContainsSubset({"page": 3, "limit": 10, "total": 101}, data)
        self.assertDictContainsSubset(
            objects[0], {"id": 21, "barcode": "product_21", "brand_id": 21}
        )

    def test_limit_without_page(self):
        resp = self.superuser_client.get("/product?_limit=10")
        data = resp.json()
        objects = data["objects"]

        self.assertDictContainsSubset({"page": 1, "limit": 10, "total": 101}, data)
        self.assertEqual(len(objects), 10)
        self.assertDictContainsSubset(
            objects[2], {"id": 3, "barcode": "product_3", "brand_id": 3}
        )

    def test_key_name_single(self):
        resp = self.superuser_client.get("/product?barcode__exact=product_21")
        data = resp.json()
        objects = data["objects"]
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 1}, data)
        self.assertEqual(len(objects), 1)
        self.assertDictContainsSubset(
            objects[0], {"id": 21, "barcode": "product_21", "brand_id": 21}
        )

    def test_key_name_single_ver2(self):
        resp = self.superuser_client.get("/product?bassdssrcode__exact=product_21")
        data = resp.json()
        self.assertTrue("non_field_error" in data)

    def test_key_name_multiple_has_result(self):
        resp = self.superuser_client.get(
            "/product?barcode__exact=product_100&id__exact=100"
        )
        data = resp.json()
        objects = data["objects"]
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 1}, data)
        self.assertEqual(len(objects), 1)
        self.assertDictContainsSubset(
            objects[0], {"id": 100, "barcode": "product_100", "brand_id": None}
        )

    def test_key_name_multiple_not_has_result(self):
        resp = self.superuser_client.get(
            "/product?barcode__exact=product_21&id__exact=20"
        )
        data = resp.json()
        objects = data["objects"]
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 0}, data)
        self.assertEqual(len(objects), 0)

    def test_extend_past_page(self):
        resp = self.superuser_client.get("/product?_page=4")
        data = resp.json()
        self.assertDictEqual({"detail": "Invalid page."}, data)

    def test_extend_past_page_with_limit(self):
        resp = self.superuser_client.get("/product?_limit=40&_page=4")
        data = resp.json()
        self.assertDictEqual({"detail": "Invalid page."}, data)

    def test_key_name_array_filled_empty(self):
        resp = self.superuser_client.get(
            "/product?barcode__in[]=product_121&barcode__in[]=product_122"
        )
        data = resp.json()
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 0}, data)
        self.assertEqual(len(data["objects"]), 0)

    def test_key_name_array(self):
        resp = self.superuser_client.get(
            "/product?barcode__in[]=product_21&barcode__in[]=product_22"
        )
        data = resp.json()
        objects = data["objects"]
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 2}, data)
        self.assertEqual(len(data["objects"]), 2)
        self.assertIn({"id": 21, "barcode": "product_21", "brand_id": 21}, objects)

    def test_invalid_key(self):
        resp = self.superuser_client.get("/product?bracode=product_21")

        self.assertEqual(400, resp.status_code)

    def test_key_name_array_with_page_and_limit(self):
        resp = self.superuser_client.get(
            "/product?barcode__in[]=product_21&barcode__in[]=product_22&_limit=1&_page=2"
        )
        data = resp.json()
        self.assertDictContainsSubset({"page": 2, "limit": 1, "total": 2}, data)
        self.assertEqual(len(data["objects"]), 1)
        self.assertEquals(data["objects"][0]["barcode"], "product_22")

    def test_positive_order(self):
        resp = self.superuser_client.get("/product?_order_by=barcode")
        data = resp.json()
        objects = data["objects"]
        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 101}, data)
        self.assertDictContainsSubset(
            objects[0], {"id": 1, "barcode": "product_1", "brand_id": 1}
        )
        self.assertDictContainsSubset(
            objects[2], {"id": 100, "barcode": "product_100", "brand_id": None}
        )

    def test_negative_order(self):
        resp = self.superuser_client.get("/product?_order_by=-barcode&_page=2")
        data = resp.json()
        objects = data["objects"]
        self.assertDictContainsSubset({"page": 2, "limit": 50, "total": 101}, data)
        self.assertDictContainsSubset(
            objects[0], {"id": 54, "barcode": "product_54", "brand_id": None}
        )
        self.assertDictContainsSubset(
            objects[1], {"id": 53, "barcode": "product_53", "brand_id": 53}
        )

    def test_order_multiple_keys(self):
        resp = self.superuser_client.get(
            "/product", {"_order_by": "-barcode,id", "_limit": 3}
        )
        data = resp.json()
        objects = data["objects"]
        self.assertEquals(3, len(objects))
        self.assertDictEqual(
            objects[0], {"id": 99, "barcode": "product_99", "brand_id": 99}
        )
        self.assertDictEqual(
            objects[1], {"id": 101, "barcode": "product_99", "brand_id": None}
        )
        self.assertDictEqual(
            objects[2], {"id": 98, "barcode": "product_98", "brand_id": None}
        )

    def test_order_malformed(self):
        resp = self.superuser_client.get("/product?_order_by=bracode")
        self.assertEquals(400, resp.status_code)
