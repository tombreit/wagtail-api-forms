# Generated by Django 5.1.5 on 2025-01-29 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('formpages', '0007_alter_userformfield_help_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='formpage',
            name='allowed_document_file_types',
            field=models.CharField(default='.pdf, .txt', help_text="Comma separated list of allowed file types for document uploads. E.g. 'pdf, docx'.", max_length=255),
        ),
    ]
