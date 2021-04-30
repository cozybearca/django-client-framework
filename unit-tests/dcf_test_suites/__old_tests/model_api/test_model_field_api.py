from django.test import TestCase
from rest_framework.test import APIClient
from dcf_test_app import models as m


class TestModelFieldAPI(TestCase):
    def setUp(self):
        superuser = m.User.objects.create_superuser(username="testuser")
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(superuser)
        self.br1 = m.Brand.objects.create(name_zh="br1")
        self.br2 = m.Brand.objects.create(name_zh="br2")
        self.pr1 = m.Product.objects.create(barcode="pr1", brand=self.br1)
        self.pr2 = m.Product.objects.create(barcode="pr2", brand=self.br2)
        self.im1 = m.ProductImage.objects.create(product=self.pr1)
        self.im2 = m.ProductImage.objects.create(product=self.pr2)
        self.ca1 = self.pr1.categories.create(name="ca1")
        self.ca2 = self.pr2.categories.create(name="ca2")

    def test_get_request_on_foreign_key_field_should_succeed(self):
        resp = self.superuser_client.get(f"/product/{self.pr1.pk}/brand")
        self.assertContains(resp, "br1", msg_prefix=str(resp.content))
        self.assertNotContains(resp, "br2", msg_prefix=str(resp.content))

    def test_get_request_on_foreign_key_field_none_should_raise_404(self):
        pr3 = m.Product.objects.create(barcode="pr3", brand=None)
        resp = self.superuser_client.get(f"/product/{pr3.pk}/brand")
        self.assertEqual(resp.status_code, 404, str(resp.content))

    def test_get_request_on_foreign_key_query_params_should_be_ignored(self):
        resp = self.superuser_client.get(
            f"/product/{self.pr1.pk}/brand",
            {"pk": "1234", "asdfasdf": "adsfsdf"},
        )
        self.assertContains(resp, "br1", msg_prefix=str(resp.content))
        self.assertNotContains(resp, "br2", msg_prefix=str(resp.content))

    def test_get_malformed_field_name_should_raise_400(self):
        resp = self.superuser_client.get(f"/product/{self.pr1.pk}/asdf")
        self.assertEqual(resp.status_code, 400, str(resp.content))

        resp = self.superuser_client.get(f"/product/{self.pr1.pk}/barcode")
        self.assertEqual(resp.status_code, 400, str(resp.content))

        resp = self.superuser_client.get(f"/product/{self.pr1.pk}/brand_id")
        self.assertEqual(resp.status_code, 400, str(resp.content))

        resp = self.superuser_client.get(f"/category/{self.ca1.pk}/merge_into")
        self.assertEqual(resp.status_code, 400, str(resp.content))

    def test_post_malformed_body_should_raise_400(self):
        resp = self.superuser_client.post(
            f"/product/{self.pr1.pk}/categories",
            data='"abc"',
            format="json",
        )
        self.assertEqual(resp.status_code, 400, str(resp.content))

        resp = self.superuser_client.post(
            f"/product/{self.pr1.pk}/categories",
            data=[1, "a"],
            format="json",
        )
        self.assertEqual(resp.status_code, 400, str(resp.content))

        resp = self.superuser_client.post(
            f"/product/{self.pr1.pk}/categories",
            data=["a"],
            format="json",
        )
        self.assertEqual(resp.status_code, 400, str(resp.content))

    def test_put_request_on_foreign_key_field_should_raise_405(self):
        resp = self.superuser_client.put(
            f"/product/{self.pr1.pk}/brand",
            data=self.br2.pk,
            format="json",
        )
        self.assertEqual(resp.status_code, 405, str(resp.content))

    def test_post_request_on_foreign_key_field_should_raise_405(self):
        resp = self.superuser_client.post(
            f"/product/{self.pr1.pk}/brand",
            data=self.br2.pk,
            format="json",
        )
        self.assertEqual(resp.status_code, 405, str(resp.content))

    def test_delete_request_on_foreign_key_field_should_raise_405(self):
        resp = self.superuser_client.delete(f"/product/{self.pr1.pk}/brand")
        self.assertEqual(resp.status_code, 405, str(resp.content))

    def test_patch_request_on_foreign_key_field_should_raise_405(self):
        resp = self.superuser_client.patch(
            f"/product/{self.pr1.pk}/brand",
            data=self.br2.pk,
            format="json",
        )
        self.assertEqual(resp.status_code, 405, str(resp.content))

    def test_get_request_on_m2m_field_should_succeed(self):
        self.pr1.categories.add(self.ca2)
        resp = self.superuser_client.get(f"/product/{self.pr1.pk}/categories")
        self.assertContains(resp, "ca1", msg_prefix=str(resp.content))
        self.assertContains(resp, "ca2", msg_prefix=str(resp.content))

        self.ca1.products.add(self.pr2)
        resp = self.superuser_client.get(f"/category/{self.ca1.pk}/products")
        self.assertContains(resp, "pr1", msg_prefix=str(resp.content))
        self.assertContains(resp, "pr2", msg_prefix=str(resp.content))

    def test_get_request_on_m2o_field_should_succeed(self):
        self.pr1.images.add(self.im2)
        resp = self.superuser_client.get(f"/product/{self.pr1.pk}/images")
        self.assertContains(resp, f'"id":{self.im1.pk}', msg_prefix=str(resp.content))
        self.assertContains(resp, f'"id":{self.im2.pk}', msg_prefix=str(resp.content))

    def test_get_request_on_m2m_field_with_filter(self):
        self.pr1.categories.add(self.ca2)
        resp = self.superuser_client.get(
            f"/product/{self.pr1.pk}/categories",
            {"name": "ca1"},
        )
        self.assertContains(resp, "ca1", msg_prefix=str(resp.content))
        self.assertNotContains(resp, "ca2", msg_prefix=str(resp.content))

    def test_post_request_on_m2m_field(self):
        self.assertNotIn(self.ca2, self.pr1.categories.all())
        resp = self.superuser_client.post(
            f"/product/{self.pr1.pk}/categories",
            data=[self.ca2.pk],
            format="json",
        )
        self.assertContains(resp, "ca2", msg_prefix=str(resp.content))
        self.assertEqual(self.pr1.categories.count(), 2)
        self.assertIn(self.ca2, self.pr1.categories.all())

    def test_delete_request_on_m2m_field(self):
        self.assertNotIn(self.ca2, self.pr1.categories.all())
        resp = self.superuser_client.delete(
            f"/product/{self.pr1.pk}/categories",
            data=[self.ca1.pk],
            format="json",
        )
        self.assertEqual(resp.status_code, 200, str(resp.content))
        self.assertEqual(m.Category.objects.count(), 2)
        self.assertFalse(self.pr1.categories.exists())

    def test_put_request_on_m2m_field(self):
        self.assertIn(self.ca1, self.pr1.categories.all())
        self.assertNotIn(self.ca2, self.pr1.categories.all())
        resp = self.superuser_client.put(
            f"/product/{self.pr1.pk}/categories",
            data=[self.ca2.pk],
            format="json",
        )
        self.assertContains(resp, "ca2", msg_prefix=str(resp.content))
        self.assertIn(self.ca2, self.pr1.categories.all())
        self.assertNotIn(self.ca1, self.pr1.categories.all())

    def test_patch_request_on_m2m_field_should_raise_405(self):
        resp = self.superuser_client.patch(
            f"/product/{self.pr1.pk}/categories",
            data=[self.ca2.pk],
            format="json",
        )
        self.assertEqual(resp.status_code, 405, str(resp.content))
