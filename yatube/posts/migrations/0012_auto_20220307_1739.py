# Generated by Django 2.2.16 on 2022-03-07 14:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_follow'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='create',
            new_name='created',
        ),
    ]
