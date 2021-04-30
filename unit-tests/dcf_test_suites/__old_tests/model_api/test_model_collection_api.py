from django.test import TestCase
from rest_framework.test import APIClient
from dcf_test_app import models as m


class TestModelCollectionAPI(TestCase):
    def setUp(self):
        superuser = m.User.objects.create_superuser(username="testuser")
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(superuser)
        self.br1 = m.Brand.objects.create(name_zh="br1")
        self.br2 = m.Brand.objects.create(name_zh="br2")
        self.pr1 = m.Product.objects.create(barcode="pr1", brand=self.br1)
        self.pr2 = m.Product.objects.create(barcode="pr2", brand=self.br2)
        self.ca1 = self.pr1.categories.create(name="ca1")
        self.ca2 = self.pr2.categories.create(name="ca2")

    def test_get_from_model_collection(self):
        resp = self.superuser_client.get("/product")
        self.assertContains(resp, "pr1", msg_prefix=str(resp.content))
        self.assertContains(resp, "pr2", msg_prefix=str(resp.content))

        resp = self.superuser_client.get("/category")
        self.assertContains(resp, "ca1", msg_prefix=str(resp.content))
        self.assertContains(resp, "ca2", msg_prefix=str(resp.content))

        resp = self.superuser_client.get("/brand")
        self.assertContains(resp, "br1", msg_prefix=str(resp.content))
        self.assertContains(resp, "br2", msg_prefix=str(resp.content))

    def test_get_request_with_pagination(self):
        resp = self.superuser_client.get("/product", {"_limit": 1, "_page": 1})
        self.assertContains(resp, "pr1", msg_prefix=str(resp.content))
        self.assertNotContains(resp, "pr2", msg_prefix=str(resp.content))
        resp = self.superuser_client.get("/product", {"_limit": 1, "_page": 2})
        self.assertContains(resp, "pr2", msg_prefix=str(resp.content))
        self.assertNotContains(resp, "pr1", msg_prefix=str(resp.content))

    def test_get_request_with_filter(self):
        resp = self.superuser_client.get("/product", {"barcode": "pr1"})
        self.assertContains(resp, "pr1", msg_prefix=str(resp.content))
        self.assertNotContains(resp, "pr2", msg_prefix=str(resp.content))
        self.assertEqual(resp.json()["objects"][0]["barcode"], "pr1")

    def test_get_request_with_filter_by_in(self):
        resp = self.superuser_client.get("/product", {"barcode__in[]": ["pr1", "pr2"]})
        self.assertContains(resp, "pr1", msg_prefix=str(resp.content))
        self.assertContains(resp, "pr2", msg_prefix=str(resp.content))
        self.assertEqual(resp.json()["objects"][0]["barcode"], "pr1")
        self.assertEqual(resp.json()["objects"][1]["barcode"], "pr2")

    def test_get_request_with_filter_multiple_keys(self):
        resp = self.superuser_client.get(
            "/product", {"barcode": ["pr1"], "pk": [self.pr1.pk]}
        )
        self.assertContains(resp, "pr1", msg_prefix=str(resp.content))
        self.assertNotContains(resp, "pr2", msg_prefix=str(resp.content))
        self.assertEqual(resp.json()["objects"][0]["barcode"], "pr1")

    def test_get_request_with_malformed_filter(self):
        resp = self.superuser_client.get("/product", {"barcode[]": ["pr1", "pr2"]})
        self.assertEqual(resp.status_code, 200, str(resp.content))
        self.assertEqual(0, resp.json()["total"])

        resp = self.superuser_client.get("/product", {"asdfasdfasdf": "asdfasdfasd"})
        self.assertEqual(resp.status_code, 400)

    def test_get_request_with_order_by(self):
        resp = self.superuser_client.get("/product", {"_order_by": "id"})
        self.assertContains(resp, "pr1", msg_prefix=str(resp.content))
        self.assertContains(resp, "pr2", msg_prefix=str(resp.content))
        self.assertEqual(resp.json()["objects"][0]["barcode"], "pr1")
        self.assertEqual(resp.json()["objects"][1]["barcode"], "pr2")

    def test_get_request_with_order_by_reverse(self):
        resp = self.superuser_client.get("/product", {"_order_by": "-id"})
        self.assertContains(resp, "pr1", msg_prefix=str(resp.content))
        self.assertContains(resp, "pr2", msg_prefix=str(resp.content))
        self.assertEqual(resp.json()["objects"][0]["barcode"], "pr2")
        self.assertEqual(resp.json()["objects"][1]["barcode"], "pr1")

    def test_get_request_with_order_by_multiple_keys(self):
        resp = self.superuser_client.get("/product", {"_order_by": ["-id", "barcode"]})
        self.assertContains(resp, "pr1", msg_prefix=str(resp.content))
        self.assertContains(resp, "pr2", msg_prefix=str(resp.content))
        self.assertEqual(resp.json()["objects"][0]["barcode"], "pr2")
        self.assertEqual(resp.json()["objects"][1]["barcode"], "pr1")

    def test_get_request_with_order_by_malformed(self):
        resp = self.superuser_client.get("/product", {"_order_by": "id-"})
        self.assertEqual(resp.status_code, 400)

    def test_post_to_model_collection(self):
        resp = self.superuser_client.post("/brand", {"name_zh": "br3"})
        self.assertContains(resp, "br3", msg_prefix=str(resp.content), status_code=201)

        resp = self.superuser_client.post("/product", {"barcode": "pr3"})
        self.assertContains(resp, "pr3", msg_prefix=str(resp.content), status_code=201)

        resp = self.superuser_client.post("/category", {"name": "ca3"})
        self.assertContains(resp, "ca3", msg_prefix=str(resp.content), status_code=201)

        self.assertTrue(m.Product.objects.filter(barcode="pr3").exists())
        self.assertTrue(m.Category.objects.filter(name="ca3").exists())
        self.assertTrue(m.Brand.objects.filter(name_zh="br3").exists())

    def test_post_request_missing_field_should_raise_400(self):
        resp = self.superuser_client.post("/product", {"asdfwr": "br3"})
        self.assertEqual(resp.status_code, 400)

    def test_post_request_constraints_violation_should_raise_400(self):
        resp = self.superuser_client.post("/product", {"barcode": "pr1"})
        self.assertEqual(resp.status_code, 400)

    def test_malformed_get_request_query_params_should_raise_400(self):
        resp = self.superuser_client.get("/product", {"asdflkjlcvjarwer": "adfasdf"})
        self.assertEqual(resp.status_code, 400)

    def test_malformed_post_request_body_should_raise_400(self):
        resp = self.superuser_client.post(
            "/brand",
            data="asdfasdfasdf",
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_delete_is_not_allowed(self):
        resp = self.superuser_client.delete("/product")
        self.assertEqual(resp.status_code, 405)

    def test_patch_is_not_allowed(self):
        resp = self.superuser_client.patch("/product")
        self.assertEqual(resp.status_code, 405, str(resp.content))

    def test_put_is_not_allowed(self):
        resp = self.superuser_client.put("/product")
        self.assertEqual(resp.status_code, 405)

    def test_fulltext_search(self):
        resp = self.superuser_client.get("/product", {"_fulltext": "br1"})
        self.assertEqual(resp.status_code, 200, str(resp.content))
        self.assertContains(resp, "pr1", msg_prefix=str(resp.content))
        self.assertNotContains(resp, "pr2", msg_prefix=str(resp.content))
