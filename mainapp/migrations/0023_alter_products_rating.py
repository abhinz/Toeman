# Generated by Django 4.2.6 on 2023-11-30 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0022_products_rating'),
    ]

    operations = [
        migrations.AlterField(
            model_name='products',
            name='rating',
            field=models.FloatField(default=0),
        ),
    ]
