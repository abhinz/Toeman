# Generated by Django 4.2.6 on 2023-11-16 07:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orderapp', '0004_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='order',
            field=models.ForeignKey(default=130, on_delete=django.db.models.deletion.CASCADE, to='orderapp.order'),
            preserve_default=False,
        ),
    ]
