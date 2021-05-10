# from django.test import TestCase
# from rest_framework.test import APIClient
# from django.contrib.auth import get_user_model
# from dcf_test_app.models import Product


# class Test404(TestCase):
#     def setUp(self):
#         User = get_user_model()
#         self.superuser = User.objects.create_superuser(username="testuser")
#         self.superuser_client = APIClient()
#         self.superuser_client.force_authenticate(self.superuser)
#         self.product = Product.objects.create(barcode="product", brand=None)

#     def test_404(self):
#         resp = self.superuser_client.get("/product/1/brand")
#         self.assertEqual(resp.status_code, 404)
