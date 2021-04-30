from django.test import TestCase
from rest_framework.test import APIClient
from dcf_test_app import models as m
from dcf_test_app import permissions as p


class TestModelFieldAPIPermissions(TestCase):
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

    def test_get_fk_with_no_permission_on_model_object_should_raise_404(self):
        p.set_perms_shortcut(self.user, m.Brand, "r")
        resp = self.user_client.get(f"/product/{self.pr1.pk}/brand")
        self.assertEqual(resp.status_code, 404)

    def test_get_fk_with_no_permission_on_related_object_should_raise_404(self):
        p.set_perms_shortcut(self.user, m.Product, "r")
        resp = self.user_client.get(f"/product/{self.pr1.pk}/brand")
        self.assertEqual(resp.status_code, 404)

    def test_get_m2m_with_no_permission_on_model_object_should_raise_404(self):
        p.set_perms_shortcut(self.user, m.Category, "r")
        resp = self.user_client.get(f"/product/{self.pr1.pk}/categories")
        self.assertEqual(resp.status_code, 404)

    def test_get_m2m_with_no_permission_on_related_object_should_return_empty(self):
        p.set_perms_shortcut(self.user, m.Product, "r")
        resp = self.user_client.get(f"/product/{self.pr1.pk}/categories")
        data = resp.json()
        self.assertDictContainsSubset({"total": 0}, data)
        self.assertEqual(resp.status_code, 200)

    def test_get_m2m_with_read_perm_on_half_related_objects_should_return_half(self):
        self.pr1.categories.add(self.ca2)
        self.assertEqual(self.pr1.categories.count(), 2)
        p.set_perms_shortcut(self.user, m.Product, "r")
        p.set_perms_shortcut(self.user, self.ca2, "r")
        resp = self.user_client.get(f"/product/{self.pr1.pk}/categories")
        data = resp.json()
        self.assertContains(resp, "ca2")
        self.assertNotContains(resp, "ca1")
        self.assertDictContainsSubset({"total": 1}, data)
        self.assertEqual(resp.status_code, 200)

    def test_post_m2m_with_no_permission_should_raise_404(self):
        resp = self.user_client.post(
            f"/product/{self.pr1.pk}/categories",
            [self.ca2.pk],
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_post_m2m_with_r_should_raise_403(self):
        p.set_perms_shortcut(self.user, m.Product, "r")
        resp = self.user_client.post(
            f"/product/{self.pr1.pk}/categories",
            [self.ca2.pk],
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_post_m2m_with_w_w_should_succeed(self):
        p.set_perms_shortcut(self.user, m.Product, "w")
        p.set_perms_shortcut(self.user, m.Category, "w")
        self.assertEqual(self.pr1.categories.count(), 1)
        resp = self.user_client.post(
            f"/product/{self.pr1.pk}/categories",
            [self.ca2.pk],
            format="json",
        )
        self.assertEqual(resp.status_code, 200, str(resp.content))
        self.assertEqual(self.pr1.categories.count(), 2)

    def test_post_m2m_with_rw_r_should_raise_403(self):
        p.set_perms_shortcut(self.user, m.Product, "rw")
        p.set_perms_shortcut(self.user, m.Category, "r")
        resp = self.user_client.post(
            f"/product/{self.pr1.pk}/categories",
            [self.ca2.pk],
            format="json",
        )
        self.assertEqual(resp.status_code, 403, str(resp.content))

    def test_post_m2m_with_r_rw_should_raise_403(self):
        p.set_perms_shortcut(self.user, m.Product, "r")
        p.set_perms_shortcut(self.user, m.Category, "rw")
        resp = self.user_client.post(
            f"/product/{self.pr1.pk}/categories",
            [self.ca2.pk],
            format="json",
        )
        self.assertEqual(resp.status_code, 403, str(resp.content))

    def test_post_m2m_with_x_rw_should_raise_404(self):
        p.set_perms_shortcut(self.user, m.Category, "rw")
        resp = self.user_client.post(
            f"/product/{self.pr1.pk}/categories",
            [self.ca2.pk],
            format="json",
        )
        self.assertEqual(resp.status_code, 404, str(resp.content))

    def test_post_m2m_with_rw_x_should_raise_404(self):
        p.set_perms_shortcut(self.user, m.Product, "rw")
        resp = self.user_client.post(
            f"/product/{self.pr1.pk}/categories",
            [self.ca2.pk],
            format="json",
        )
        self.assertEqual(resp.status_code, 404, str(resp.content))
