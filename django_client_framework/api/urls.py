from django.urls import path

from .ModelCollectionAPI import ModelCollectionAPI
from .ModelObjectAPI import ModelObjectAPI
from .ModelFieldAPI import ModelFieldAPI

urlpatterns = [
    path("<str:model>", ModelCollectionAPI.as_view(), name="model_collection"),
    path("<str:model>/<int:pk>", ModelObjectAPI.as_view(), name="model_object"),
    path(
        "<str:model>/<int:pk>/<str:target_field>",
        ModelFieldAPI.as_view(),
        name="model_field",
    ),
]
