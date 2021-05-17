from django.test import TestCase
from rest_framework.test import APIClient
from dcf_test_app.models import Product
from dcf_test_app.models import Brand
from django.contrib.auth.models import User
from django_client_framework import permissions as p


class PostPerms(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.br1 = Brand.objects.create(name="br1")
        self.br2 = Brand.objects.create(name="br2")
        self.pr1 = Product.objects.create(barcode="pr1", brand=self.br1)
        self.pr2 = Product.objects.create(barcode="pr2", brand=self.br2)

        p.clear_permissions()

    def test_post_without_permissions(self):
        resp = self.user_client.post("/product", {"barcode": "pr3"})
        self.assertEqual(403, resp.status_code)

    def test_post_only_read_permissions(self):
        p.set_perms_shortcut(self.user, Product, "r")
        resp = self.user_client.post("/product", {"barcode": "pr3"})
        self.assertEqual(403, resp.status_code)

    def test_post_only_create_permissions(self):
        p.set_perms_shortcut(self.user, Product, "c")
        resp = self.user_client.post("/product", {"barcode": "pr3"})
        data = resp.json()
        self.assertDictEqual(
            data,
            {
                "success": True,
                "info": "The object has been created but you have no permission to view it.",
            },
        )

    def test_post_wrong_object_permissions(self):
        p.set_perms_shortcut(self.user, Product.objects.get(id=1), "rc")
        resp = self.user_client.post("/product", {"asdf": "pr3"})
        self.assertEqual(403, resp.status_code)

    def test_post_invalid_dict(self):
        p.set_perms_shortcut(self.user, Product, "rc")
        resp = self.user_client.post("/product", {"asdf": "pr3"})
        self.assertEqual(400, resp.status_code)
        self.assertTrue("non_field_error" in resp.json())

    def test_post_read_create_permissions(self):
        p.set_perms_shortcut(self.user, Product, "rc")
        resp = self.user_client.post("/product", {"barcode": "pr3"})
        data = resp.json()
        self.assertDictEqual({"id": 3, "barcode": "pr3", "brand_id": None}, data)

    def test_post_read_create_permissions_ver2(self):
        p.set_perms_shortcut(self.user, Product, "rc")
        resp = self.user_client.post("/product", {"asdf": "pr3"})
        data = resp.json()
        self.assertTrue("non_field_error" in data)

    def test_post_read_create_permissions_ver3(self):
        p.set_perms_shortcut(self.user, Product, "rc")
        resp = self.user_client.post("/product", {"barcode": "pr3"})
        data = resp.json()
        self.assertDictEqual({"id": 3, "barcode": "pr3", "brand_id": None}, data)

    def test_post_with_fk_without_permissions(self):
        p.set_perms_shortcut(self.user, Product, "c")
        resp = self.user_client.post("/product", {"barcode": "pr3", "brand_id": 1})
        self.assertEquals(resp.status_code, 404)

    def test_post_with_fk_incorrect_perm(self):
        p.set_perms_shortcut(self.user, Product, "c")
        p.set_perms_shortcut(self.user, Brand, "rcd")
        resp = self.user_client.post("/product", {"barcode": "pr3", "brand_id": 1})
        self.assertEquals(resp.status_code, 403)

    def test_post_with_fk_with_permissions(self):
        p.set_perms_shortcut(self.user, Product, "rc")
        p.set_perms_shortcut(self.user, Brand, "w")
        resp = self.user_client.post("/product", {"barcode": "pr3", "brand_id": 1})
        data = resp.json()
        self.assertDictEqual(data, {"id": 3, "barcode": "pr3", "brand_id": 1})

    def test_post_with_fk_with_permissions_2(self):
        p.set_perms_shortcut(self.user, Product, "rc")
        p.set_perms_shortcut(self.user, Brand, "w")
        resp = self.user_client.post("/product", {"barcode": "pr3", "brand_id": 5})
        data = resp.json()
        self.assertDictEqual(
            data, {"brand_id": 'Invalid pk "5" - object does not exist.'}
        )
