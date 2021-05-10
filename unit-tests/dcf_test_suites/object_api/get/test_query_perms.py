# from django.test import TestCase
# from rest_framework.test import APIClient
# from django_client_framework import permissions as p
# from dcf_test_app.models import Product
# from dcf_test_app.models import Brand
# from django.contrib.auth.models import User

# class TestQueryPerms(TestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(username="testuser")
#         self.user_client = APIClient()
#         self.user_client.force_authenticate(self.user)
#         self.br1 = Brand.objects.create(name="br1")
#         self.br2 = Brand.objects.create(name="br2")
#         self.pr1 = Product.objects.create(barcode="pr1", brand=self.br1)
#         self.pr2 = Product.objects.create(barcode="pr2", brand=self.br2)
#         p.clear_permissions()
    

#     def test_get_without_permissions(self):
#         resp = self.user_client.get("/product/1")
#         self.assertEquals(404, resp.status_code)
    

#     def test_get_incorrect_permissions(self):
#         p.set_perms_shortcut(self.user, Product, "wcd")
#         resp = self.user_client.get("/product/1")
#         self.assertEquals(404, resp.status_code)



#     def test_get_incorrect_permissions_ver_2(self):
#         p.set_perms_shortcut(self.user, Product, "r", field_name="barcode")
#         resp = self.user_client.get("/product/1")
#         self.assertEquals(404, resp.status_code)


#     def test_get_correct_permissions(self):
#         p.set_perms_shortcut(self.user, Product, "r")
#         resp = self.user_client.get("/product/1")
#         self.assertDictEqual(resp.json(), {"id": 1, "barcode": "pr1", "brand_id": 1})


#     # error: should be 403?
#     def test_patch_no_permissions(self):
#         resp = self.user_client.patch("/product/1", {"barcode": "p1"})
#         self.assertEquals(404, resp.status_code)
    

#     def test_patch_incorrect_permissions(self):
#         p.set_perms_shortcut(self.user, Product, "rcd")
#         resp = self.user_client.patch("/product/1", {"barcode": "p1"})
#         self.assertEquals(403, resp.status_code)


#     # error: should be 403?
#     def test_patch_wrong_field(self):
#         p.set_perms_shortcut(self.user, Product, "w", field_name="brand_id")
#         resp = self.user_client.patch("/product/1", {"barcode": "po1"})
#         self.assertEquals(404, resp.status_code)


#     # error: shouldn't show resulting object
#     def test_patch_correct_permissions(self):
#         p.set_perms_shortcut(self.user, Product, "w")
#         resp = self.user_client.patch("/product/1", {"barcode": "po1"})
#         data = resp.json()
#         self.assertDictEqual(data, { "success": True, "info": "The object has been updated but you have no permission to view it." })
#         self.assertEquals(Product.objects.get(id=1).barcode, "po1")


#     def test_patch_correct_permissions_ver_2(self):
#         p.set_perms_shortcut(self.user, Product, "w", field_name="barcode")
#         resp = self.user_client.patch("/product/1", {"barcode": "po1"})
#         data = resp.json()
#         self.assertDictEqual(data, { "success": True, "info": "The object has been updated but you have no permission to view it." })
#         self.assertEquals(Product.objects.get(id=1).barcode, "po1")


#     def test_patch_fk_no_permissions(self):
#         resp = self.user_client.patch("/product/1", { "brand_id": 2 })
#         self.assertEquals(404, resp.status_code)


#     def test_patch_fk_no_permissions_except_product_w(self):
#         p.set_perms_shortcut(self.user, Product, "w", field_name="brand_id")
#         resp = self.user_client.patch("/product/1", { "brand_id": 2 })
#         self.assertEquals(404, resp.status_code)

    
#     def test_patch_fk_incorrect_perms(self):
#         p.set_perms_shortcut(self.user, Product, "w", field_name="brand_id")
#         p.set_perms_shortcut(self.user, Brand, "rcd")
#         resp = self.user_client.patch("/product/1", { "brand_id": 2 })
#         self.assertEquals(404, resp.status_code)


#     # error: shouldn't show the resulting product
#     def test_patch_fk_correct_perms(self):
#         p.set_perms_shortcut(self.user, Product, "w", field_name="brand")
#         p.set_perms_shortcut(self.user, Brand, "rwcd")
#         resp = self.user_client.patch("/product/1", { "brand_id": 2 })
#         data = resp.json()
#         self.assertDictEqual(data, { "success": True, "info": "The object has been updated but you have no permission to view it." })
#         self.assertEquals(Product.objects.get(id=1).brand_id, 2)