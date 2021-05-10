from django.contrib.auth.models import Group, Permission
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import *
from django_client_framework.models import *
from .brand import *
from .product import *