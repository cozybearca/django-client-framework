from django.test import TestCase
from rest_framework.test import APIClient
from dcf_test_app import models as m
from dcf_test_app import permissions as p


class TestModelCollectionAPIPermissions(TestCase):
    def setUp(self):
        self.user = m.User.objects.create_user(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.br1 = m.Brand.objects.create(name_zh="br1")
        self.br2 = m.Brand.objects.create(name_zh="br2")
        self.pr1 = m.Product.objects.create(barcode="pr1", brand=self.br1)
        self.pr2 = m.Product.objects.create(barcode="pr2", brand=self.br2)
        self.ca1 = self.pr1.categories.create(name="ca1")
        self.ca2 = self.pr2.categories.create(name="ca2")
        p.clear_permissions()

    def test_get_with_no_permission_should_return_empty(self):
        resp = self.user_client.get("/product")
        data = resp.json()
        self.assertDictContainsSubset({"total": 0, "objects": []}, data)
        self.assertEqual(resp.status_code, 200)

    def test_get_with_model_r_should_return_all_objects(self):
        p.set_perms_shortcut(self.user, m.Product, "r")
        resp = self.user_client.get("/product")
        data = resp.json()
        self.assertDictContainsSubset({"total": 2}, data)
        self.assertEqual(resp.status_code, 200)

    def test_get_with_object_r_on_one_object_should_return_one_object(self):
        p.set_perms_shortcut(self.user, self.pr1, "r")
        resp = self.user_client.get("/product")
        data = resp.json()
        self.assertContains(resp, "pr1")
        self.assertNotContains(resp, "pr2")
        self.assertDictContainsSubset({"total": 1}, data)
        self.assertEqual(resp.status_code, 200)

    def test_post_with_no_permission_should_raise_403(self):
        resp = self.user_client.post("/product", {"barcode": "0"})
        self.assertEqual(resp.status_code, 403, str(resp.content))

    def test_post_with_rc_permission_should_respond_object(self):
        p.set_perms_shortcut(self.user, m.Product, "rc")
        resp = self.user_client.post("/product", {"barcode": "pr3"})
        self.assertContains(resp, "pr3", status_code=201, msg_prefix=str(resp.content))

    def test_post_fk_with_model_c_relobj_w_should_succeed(self):
        p.set_perms_shortcut(self.user, m.Product, "c")
        p.set_perms_shortcut(self.user, m.Brand, "w")
        resp = self.user_client.post(
            "/product",
            {"barcode": "pr3", "brand_id": self.br2.pk},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, str(resp.content))

    def test_post_fk_with_model_c_relobj_w_none_should_succeed(self):
        p.set_perms_shortcut(self.user, m.Product, "c")
        p.set_perms_shortcut(self.user, m.Brand, "w")
        resp = self.user_client.post(
            "/product",
            {"barcode": "pr3", "brand_id": None},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, str(resp.content))

    def test_post_fk_with_model_rwcd_relobj_rcd_should_raise_403_case_1(self):
        # case 1
        p.set_perms_shortcut(self.user, m.Product, "rwcd")
        p.set_perms_shortcut(self.user, m.Brand, "rcd")  # no write
        resp = self.user_client.post(
            "/product",
            {"barcode": "pr3", "brand_id": self.br2.pk},
            format="json",
        )
        self.assertEqual(resp.status_code, 403, str(resp.content))

    def test_post_fk_with_model_rwcd_relobj_rcd_should_raise_403_case_2(self):
        # case 2
        p.set_perms_shortcut(self.user, m.Product, "rcd")  # no write
        p.set_perms_shortcut(self.user, m.Basket, "rwcd")
        p.set_perms_shortcut(self.user, m.BasketProduct, "c")
        resp = self.user_client.post(
            "/basketproduct",
            format="json",
            data={
                "product_id": self.pr1.pk,
                "basket_id": self.user.basket.pk,
            },
        )
        self.assertEqual(resp.status_code, 403, str(resp.content))

    def test_post_fk_with_model_c_relob_field_w_should_succeed(self):
        p.set_perms_shortcut(self.user, m.Product, "w", field_name="basketproduct")
        p.set_perms_shortcut(self.user, m.Basket, "w")
        p.set_perms_shortcut(self.user, m.BasketProduct, "c")
        resp = self.user_client.post(
            "/basketproduct",
            format="json",
            data={
                "product_id": self.pr1.pk,
                "basket_id": self.user.basket.pk,
            },
        )
        self.assertEqual(resp.status_code, 201, str(resp.content))

    def test_post_fk_with_model_rwcd_relobj_cd_should_raise_404(self):
        p.set_perms_shortcut(self.user, m.Product, "rwcd")
        p.set_perms_shortcut(self.user, m.Brand, "cd")
        resp = self.user_client.post(
            "/product",
            {"barcode": "pr3", "brand_id": self.br2.pk},
            format="json",
        )
        self.assertEqual(resp.status_code, 404, str(resp.content))
