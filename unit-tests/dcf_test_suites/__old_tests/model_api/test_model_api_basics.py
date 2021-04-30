from django.test import Client, TestCase


class TestModelAPIBasics(TestCase):
    def test_invalid_model_name(self):
        resp = Client().get("/abc")
        self.assertEqual(resp.status_code, 400)
