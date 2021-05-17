# Generated by Django 3.1.4 on 2021-05-08 07:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dcf_test_app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
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
                ("username", models.CharField(max_length=100, null=True, unique=True)),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
