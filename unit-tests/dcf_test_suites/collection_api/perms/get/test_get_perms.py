from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from dcf_test_app.models import Product
from dcf_test_app.models import Brand
from django.contrib.auth.models import User
from django_client_framework import permissions as p


class GetPerms(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.br1 = Brand.objects.create(name="br1")
        self.br2 = Brand.objects.create(name="br2")
        self.pr1 = Product.objects.create(barcode="pr1", brand=self.br1)
        self.pr2 = Product.objects.create(barcode="pr2", brand=self.br2)

        p.clear_permissions()

    
    def test_get_without_permissions(self):
        resp = self.user_client.get("/product")
        data = resp.json()
        self.assertDictContainsSubset({"total": 0, "objects": []}, data)
        self.assertEqual(resp.status_code, 200)
    

    def test_incorrect_permissions(self):
        p.set_perms_shortcut(self.user, Product, "wcd")
        resp = self.user_client.get("/product")
        data = resp.json()
        self.assertDictContainsSubset({"total": 0, "objects": []}, data)
        self.assertEqual(resp.status_code, 200)
    
    
    def test_get_all_with_model_permissions(self):
        p.set_perms_shortcut(self.user, Product, "r")
        resp = self.user_client.get("/product")
        data = resp.json()

        self.assertDictContainsSubset({"page": 1, "limit": 50, "total": 2}, data)
        objects = data["objects"]
        self.assertDictEqual(objects[0], {"barcode": "pr1", "brand_id": 1, "id": 1})
    

    def test_get_r_on_object(self):
        p.set_perms_shortcut(self.user, self.pr2, "r")
        resp = self.user_client.get("/product")
        data = resp.json()
        self.assertDictContainsSubset({ "page": 1, "limit": 50, "total": 1 }, data)
        objects = data["objects"]
        self.assertDictEqual(objects[0], {"barcode": "pr2", "brand_id": 2, "id": 2})
