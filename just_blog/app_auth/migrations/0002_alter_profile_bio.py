# Generated by Django 4.2 on 2023-04-30 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_auth', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='bio',
            field=models.CharField(blank=True, max_length=256, verbose_name='bio'),
        ),
    ]
