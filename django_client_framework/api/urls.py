from django.urls import path

from .model_collection_api import ModelCollectionAPI
from .model_object_api import ModelObjectAPI
from .related_model_api import RelatedModelAPI

urlpatterns = [
    path("<str:model>", ModelCollectionAPI.as_view(), name="model_collection"),
    path("<str:model>/<int:pk>", ModelObjectAPI.as_view(), name="model_object"),
    path(
        "<str:model>/<int:pk>/<str:target_field>",
        RelatedModelAPI.as_view(),
        name="related_model",
    ),
]
