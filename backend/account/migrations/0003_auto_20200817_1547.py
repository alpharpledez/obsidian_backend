# Generated by Django 3.0.5 on 2020-08-17 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_auto_20200816_1023'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='m_type',
            field=models.CharField(default='', max_length=30),
        ),
        migrations.AlterField(
            model_name='myuser',
            name='first_name',
            field=models.CharField(blank=True, max_length=30, verbose_name='first name'),
        ),
    ]