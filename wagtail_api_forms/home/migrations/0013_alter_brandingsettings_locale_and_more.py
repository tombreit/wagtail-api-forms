# Generated by Django 5.1.2 on 2024-10-16 20:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0012_brandingsettings_show_admin_link_for_ips'),
        ('wagtailcore', '0094_alter_page_locale'),
    ]

    operations = [
        migrations.AlterField(
            model_name='brandingsettings',
            name='locale',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale'),
        ),
        migrations.AlterField(
            model_name='footerlinks',
            name='locale',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale'),
        ),
    ]
