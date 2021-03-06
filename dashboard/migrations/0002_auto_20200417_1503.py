# Generated by Django 3.0.4 on 2020-04-17 12:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customers',
            old_name='city_name',
            new_name='customer_name',
        ),
        migrations.RenameField(
            model_name='sales',
            old_name='customer_id',
            new_name='customer',
        ),
        migrations.RenameField(
            model_name='shipping',
            old_name='customer_id',
            new_name='customer',
        ),
        migrations.RenameField(
            model_name='shipping',
            old_name='supplier_id',
            new_name='supplier',
        ),
        migrations.RenameField(
            model_name='suppliers',
            old_name='city_name',
            new_name='supplier_name',
        ),
    ]
