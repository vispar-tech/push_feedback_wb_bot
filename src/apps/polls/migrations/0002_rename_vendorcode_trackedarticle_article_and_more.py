# Generated by Django 4.1.7 on 2023-03-07 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='trackedarticle',
            old_name='vendorCode',
            new_name='article',
        ),
        migrations.AddField(
            model_name='trackedarticle',
            name='brand',
            field=models.CharField(blank=True, max_length=255, verbose_name='Бренд'),
        ),
        migrations.AddField(
            model_name='trackedarticle',
            name='name',
            field=models.TextField(default=None, verbose_name='Наименование'),
            preserve_default=False,
        ),
    ]
