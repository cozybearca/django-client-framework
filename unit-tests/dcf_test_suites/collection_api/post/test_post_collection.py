from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from dcf_test_app.models import Product
from dcf_test_app.models import Brand

class TestPostCollection(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(username="testuser")
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(self.superuser)
        self.brands = [Brand.objects.create(name=f"name_{i+1}") for i in range(100)]


    def test_post_brand(self):
        self.assertEquals(100, Brand.objects.count())
        resp = self.superuser_client.post("/brand", { "name": "test_brand" })
        self.assertEquals(101, Brand.objects.count())

        obj = resp.json()
        self.assertDictContainsSubset(
            obj,
            {"id": 101, "name": "test_brand" }
        )
        self.assertTrue(Brand.objects.filter(name="test_brand").exists())


    def test_post_brand(self):
        self.assertEquals(100, Brand.objects.count())
        resp = self.superuser_client.post("/brand", { "namaae": "test_brand" })
        self.assertEquals(100, Brand.objects.count())
        data = resp.json()
        self.assertTrue("non_field_error" in data)

    
    def test_post(self):
        self.assertEquals(0, Product.objects.count())
        resp = self.superuser_client.post("/product", { "barcode": "unique", "brand_id": 1 })
        self.assertEquals(1, Product.objects.count())
        self.assertTrue(Product.objects.filter(barcode="unique").exists())
        self.assertDictEqual(resp.json(), {"id": 1, "barcode": "unique", "brand_id": 1})


    def test_post_invalid_fk(self):
        self.assertEquals(0, Product.objects.count())
        resp = self.superuser_client.post("/product", { "barcode": "unique", "brand_id": 200 })
        self.assertEquals(0, Product.objects.count())
        self.assertDictEqual(resp.json(), {'brand_id': 'Invalid pk "200" - object does not exist.'})