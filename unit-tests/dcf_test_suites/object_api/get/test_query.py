# from django.test import TestCase
# from rest_framework.test import APIClient
# from django.contrib.auth import get_user_model
# from dcf_test_app.models import Product
# from dcf_test_app.models import Brand


# class TestQuery(TestCase):
#     def setUp(self):
#         User = get_user_model()
#         self.superuser = User.objects.create_superuser(username="testuser")
#         self.superuser_client = APIClient()
#         self.superuser_client.force_authenticate(self.superuser)
#         self.brands = [Brand.objects.create(name=f"name_{i+1}") for i in range(2)]
#         self.products = [
#             Product.objects.create(
#                 barcode=f"product_{i+1}", brand=self.brands[i] if i % 2 == 0 else None
#             )
#             for i in range(2)
#         ]

#     def test_get_1(self):
#         resp = self.superuser_client.get("/product/1")
#         data = resp.json()
#         self.assertDictEqual(data, {"id": 1, "barcode": "product_1", "brand_id": 1})

    
#     def test_get_2(self):
#         resp = self.superuser_client.get("/product/2")
#         data = resp.json()
#         self.assertDictEqual(data, {"id": 2, "barcode": "product_2", "brand_id": None})

#     def test_get_invalid_query_params(self):
#         resp = self.superuser_client.get("/product/1", {"barcodee": "product_1", "brand_id": 1})
#         data = resp.json()
#         self.assertDictEqual(data, {"id": 1, "barcode": "product_1", "brand_id": 1})
    
#     def test_patch_successful(self):
#         resp = self.superuser_client.patch(
#             "/product/1",
#             { "barcode": "product_11", "brand_id": 2 }
#         )
#         data = resp.json()
#         self.assertDictEqual(data, { "id": 1, "barcode": "product_11", "brand_id": 2 }) 
#         self.assertEqual(Product.objects.get(id=1).barcode, "product_11")
    
#     def test_patch_invalid_keys(self):
#         resp = self.superuser_client.patch(
#             "/product/1", 
#             { "barcodee": "product_2", "brand_id": 2 }
#         )
#         data = resp.json()
#         self.assertDictEqual( data, { "non_field_error": "Extra fields are not allowed: ['barcodee'], valid fields are: ['barcode', 'brand_id']" })
        
#     # error: need proper response for trying to delete objects?
#     # def test_delete_object_invalid(self):
#     #     resp = self.superuser_client.delete(
#     #         "/product/1",
#     #         {
#     #             "barcode": "product_2"
#     #         }
#     #     )
#     #     self.assertEquals(405, resp.status_code)
    
#     def test_post_object_invalid(self):
#         resp = self.superuser_client.post(
#             "/product/1",
#             {
#                 "barcode": "product_2"
#             }
#         )
#         self.assertEquals(405, resp.status_code)
    
#     def test_put_object_invalid(self):
#         resp = self.superuser_client.put(
#             "/product/1",
#             {
#                 "barcode": "product_2"
#             }
#         )
#         self.assertEquals(405, resp.status_code)