# Generated by Django 4.2 on 2023-04-30 08:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_auth', '0001_initial'),
        ('app_blog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='profile',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='app_auth.profile'),
            preserve_default=False,
        ),
    ]