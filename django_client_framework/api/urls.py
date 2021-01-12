from django.urls import path

from . import model_api as a

urlpatterns = [
    path("<str:model>", a.ModelCollectionAPI.as_view(), name="model_collection"),
    path("<str:model>/<int:pk>", a.ModelObjectAPI.as_view(), name="model_object"),
    path(
        "<str:model>/<int:pk>/<str:target_field>",
        a.ModelFieldAPI.as_view(),
        name="model_field",
    ),
]
