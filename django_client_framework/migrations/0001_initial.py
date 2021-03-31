# Generated by Django 3.1.5 on 2021-01-11 10:14

import django.contrib.postgres.indexes
import django.contrib.postgres.search
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="SearchFeature",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("object_id", models.PositiveIntegerField(db_index=True, null=True)),
                ("text_feature", models.TextField()),
                ("search_vector", django.contrib.postgres.search.SearchVectorField()),
                (
                    "content_type",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="searchfeature",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["search_vector"], name="django_clie_search__83d87e_gin"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="searchfeature",
            unique_together={("object_id", "content_type")},
        ),
        migrations.AlterIndexTogether(
            name="searchfeature",
            index_together={("object_id", "content_type")},
        ),
    ]