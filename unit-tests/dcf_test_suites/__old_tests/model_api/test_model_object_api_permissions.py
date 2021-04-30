from django.test import TestCase
from rest_framework.test import APIClient
from dcf_test_app import models as m


class TestModelObjectAPIPermissions(TestCase):
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

    def test_patch_with_no_permission_should_raise_404(self):
        resp = self.user_client.patch(
            f"/product/{self.pr1.pk}",
            {"name_zh": "0"},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_patch_with_model_r_should_raise_403(self):
        p.set_perms_shortcut(self.user, m.Product, "r")
        resp = self.user_client.patch(
            f"/product/{self.pr1.pk}",
            {"name_zh": "0"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_patch_with_model_w_should_succeed(self):
        p.set_perms_shortcut(self.user, m.Product, "w")
        resp = self.user_client.patch(
            f"/product/{self.pr1.pk}",
            {"name_zh": "0"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)

    def test_patch_with_model_c_should_raise_404(self):
        p.set_perms_shortcut(self.user, m.Product, "c")
        resp = self.user_client.patch(
            f"/product/{self.pr1.pk}",
            {"name_zh": "0"},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_patch_with_model_d_should_raise_404(self):
        p.set_perms_shortcut(self.user, m.Product, "d")
        resp = self.user_client.patch(
            f"/product/{self.pr1.pk}",
            {"name_zh": "0"},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_patch_with_model_rc_should_raise_403(self):
        p.set_perms_shortcut(self.user, m.Product, "rc")
        resp = self.user_client.patch(
            f"/product/{self.pr1.pk}",
            {"name_zh": "0"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_patch_with_model_rd_should_raise_403(self):
        p.set_perms_shortcut(self.user, m.Product, "rd")
        resp = self.user_client.patch(
            f"/product/{self.pr1.pk}",
            {"name_zh": "0"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_patch_fk_with_model_w_relobj_w_should_succeed(self):
        p.set_perms_shortcut(self.user, m.Product, "w")
        p.set_perms_shortcut(self.user, m.Brand, "w")
        resp = self.user_client.patch(
            f"/product/{self.pr1.pk}",
            {"brand_id": self.br2.pk},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, str(resp.content))

    def test_patch_fk_with_model_w_relobj_w_none_should_succeed(self):
        p.set_perms_shortcut(self.user, m.Product, "w")
        p.set_perms_shortcut(self.user, m.Brand, "w")
        resp = self.user_client.patch(
            f"/product/{self.pr1.pk}",
            {"brand_id": None},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, str(resp.content))

    def test_patch_fk_with_model_rw_relobj_r_should_raise_403(self):
        p.set_perms_shortcut(self.user, m.Product, "rw")
        p.set_perms_shortcut(self.user, m.Brand, "r")
        resp = self.user_client.patch(
            f"/product/{self.pr1.pk}",
            {"brand_id": self.br2.pk},
            format="json",
        )
        self.assertEqual(resp.status_code, 403, str(resp.content))

    def test_patch_fk_with_model_rw_relobj_none_should_raise_404(self):
        p.set_perms_shortcut(self.user, m.Product, "rw")
        resp = self.user_client.patch(
            f"/product/{self.pr1.pk}",
            {"brand_id": self.br2.pk},
            format="json",
        )
        self.assertEqual(resp.status_code, 404, str(resp.content))

    def test_get_object_without_read_permission_should_raise_404(self):
        superuser = m.User.objects.create_user(username="superuser")
        resp = self.user_client.get(f"/user/{superuser.pk}")
        self.assertEqual(resp.status_code, 404)

    def test_delete_object_with_r_perm_should_raise_403(self):
        p.set_perms_shortcut(self.user, m.Product, "r")
        resp = self.user_client.delete(f"/product/{self.pr1.pk}")
        self.assertEqual(resp.status_code, 403)

    def test_delete_object_with_no_perm_should_raise_404(self):
        resp = self.user_client.delete(f"/product/{self.pr1.pk}")
        self.assertEqual(resp.status_code, 404)
