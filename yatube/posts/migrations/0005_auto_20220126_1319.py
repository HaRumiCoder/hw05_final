# Generated by Django 2.2.9 on 2022-01-26 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0004_auto_20220123_2025"),
    ]

    operations = [
        migrations.AlterField(
            model_name="group", name="slug", field=models.SlugField(unique=True),
        ),
        migrations.AlterField(
            model_name="group", name="title", field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="post",
            name="pub_date",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
