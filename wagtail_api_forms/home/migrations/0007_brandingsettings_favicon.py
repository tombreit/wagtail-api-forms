# Generated by Django 4.1.7 on 2023-03-23 15:10

from django.db import migrations, models
import wagtail_api_forms.home.models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_alter_customimage_file_alter_customrendition_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='brandingsettings',
            name='favicon',
            field=models.FileField(blank=True, help_text='Favicon file. Formats: ICO or PNG', null=True, upload_to='branding/', validators=[wagtail_api_forms.home.models.validate_favicon_file_extension], verbose_name='Favicon file'),
        ),
    ]
