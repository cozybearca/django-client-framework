from django.test import TestCase
from rest_framework.test import APIClient
from dcf_test_app import models as m


class TestModelObjectAPI(TestCase):
    def setUp(self):
        self.superuser = m.User.objects.create_superuser(username="testuser")
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(self.superuser)
        self.br1 = m.Brand.objects.create(name_zh="br1")
        self.br2 = m.Brand.objects.create(name_zh="br2")
        self.pr1 = m.Product.objects.create(barcode="pr1", brand=self.br1)
        self.pr2 = m.Product.objects.create(barcode="pr2", brand=self.br2)
        self.im1 = m.ProductImage.objects.create(product=self.pr1)
        self.im2 = m.ProductImage.objects.create(product=self.pr2)
        self.ca1 = self.pr1.categories.create(name="ca1")
        self.ca2 = self.pr2.categories.create(name="ca2")

    def test_get_object_should_succeed(self):
        resp = self.superuser_client.get(f"/product/{self.pr1.pk}")
        self.assertContains(resp, "pr1", msg_prefix=str(resp.content))
        resp = self.superuser_client.get(f"/category/{self.ca1.pk}")
        self.assertContains(resp, "ca1", msg_prefix=str(resp.content))
        resp = self.superuser_client.get(f"/brand/{self.br1.pk}")
        self.assertContains(resp, "br1", msg_prefix=str(resp.content))

    def test_get_request_query_params_should_be_ignored(self):
        resp = self.superuser_client.get(
            f"/product/{self.pr1.pk}",
            {"asdfasdfas": "asdfasdfasdf", "pk": "0"},
        )
        self.assertContains(resp, "pr1", msg_prefix=str(resp.content))

    def test_patch_object_should_succeed(self):
        resp = self.superuser_client.patch(
            f"/product/{self.pr1.pk}",
            {"name_en": "pr0", "name_zh": "pr0"},
            format="json",
        )
        self.assertContains(resp, "pr0", count=2, msg_prefix=str(resp.content))

    def test_patch_request_pk_field_should_raise_400(self):
        old_pk = self.pr1.pk
        resp = self.superuser_client.patch(
            f"/product/{self.pr1.pk}",
            {"id": 1234, "pk": 1234},
            format="json",
        )
        self.assertContains(
            resp,
            "Extra fields are not allowed: ['id', 'pk']",
            status_code=400,
            msg_prefix=str(resp.content),
        )

        self.assertEqual(m.Product.objects.count(), 2)
        self.assertEqual(m.Product.objects.filter(barcode="pr1").first().pk, old_pk)

    def test_patch_with_malformed_field_names_raise_400(self):
        resp = self.superuser_client.patch(
            f"/product/{self.pr1.pk}",
            {"asdfasdf": "zxcvzxcv"},
            format="json",
        )
        self.assertContains(
            resp,
            "Extra fields are not allowed: ['asdfasdf']",
            status_code=400,
            msg_prefix=str(resp.content),
        )

    def test_patch_custom_serializer_field_should_succeed(self):
        resp = self.superuser_client.patch(
            f"/category/{self.ca2.pk}",
            {"merge_into": self.ca1.pk},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, str(resp.content))

    def test_delete_object_should_succeed(self):
        resp = self.superuser_client.delete(f"/product/{self.pr1.pk}")
        self.assertEqual(resp.status_code, 204, str(resp.content))
        self.assertFalse(m.Product.objects.filter(barcode="pr1").exists())
        self.assertTrue(m.Product.objects.filter(barcode="pr2").exists())

    def test_delete_when_protected_should_raise_400(self):
        resp = self.superuser_client.delete(f"/category/{self.ca1.pk}")
        self.assertEqual(resp.status_code, 400)

    def test_delete_object_not_found_should_raise_404(self):
        resp = self.superuser_client.delete("/product/1234")
        self.assertEqual(resp.status_code, 404)

    def test_delete_request_body_should_be_ignored(self):
        resp = self.superuser_client.delete(
            f"/product/{self.pr1.pk}",
            data="asdfasdfa",
            content_type="plain/text",
        )
        self.assertEqual(resp.status_code, 204, str(resp.content))
        self.assertFalse(m.Product.objects.filter(barcode="pr1").exists())
        self.assertTrue(m.Product.objects.filter(barcode="pr2").exists())

    def test_put_is_not_allowed(self):
        resp = self.superuser_client.put(f"/product/{self.pr1.pk}")
        self.assertEqual(resp.status_code, 405, str(resp.content))

    def test_post_is_not_allowed(self):
        resp = self.superuser_client.post(f"/product/{self.pr1.pk}")
        self.assertEqual(resp.status_code, 405, str(resp.content))
