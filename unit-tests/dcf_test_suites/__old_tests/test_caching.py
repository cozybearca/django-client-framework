from django.shortcuts import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from dcf_test_app import models as m


class CachingTest(TestCase):
    def setUp(self):
        superuser = m.User.objects.create_superuser()
        self.client = APIClient()
        self.client.force_authenticate(superuser)

    def test_model_collection_api_caching(self):
        """
        When an object is changed, model api should return the updated data
        """
        products = [m.Product.objects.create(barcode=str(i)) for i in range(10)]
        response = self.client.get(
            reverse("api:v1:model_collection", kwargs={"model": "product"})
        )
        self.assertEqual(response.status_code, 200, str(response.content))
        objects = response.json()["objects"]
        self.assertEqual(len(objects), len(products))
        for p, o in zip(products, objects):
            self.assertEqual(p.barcode, o["barcode"])
            p.barcode = "1" + p.barcode
            p.save()
        # get again
        response = self.client.get(
            reverse("api:v1:model_collection", kwargs={"model": "product"})
        )
        self.assertEqual(response.status_code, 200, str(response.content))
        objects = response.json()["objects"]
        self.assertEqual(len(objects), len(products))
        for p, o in zip(products, objects):
            p.refresh_from_db()
            self.assertEqual(p.barcode, o["barcode"])
