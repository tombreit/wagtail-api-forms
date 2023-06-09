# Generated by Django 4.0.2 on 2022-02-11 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('formpages', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userformfield',
            name='field_type',
            field=models.CharField(choices=[('singleline', 'Single line text'), ('multiline', 'Multi-line text'), ('email', 'Email'), ('number', 'Number'), ('url', 'URL'), ('checkbox', 'Checkbox'), ('checkboxes', 'Checkboxes'), ('dropdown', 'Drop down'), ('multiselect', 'Multiple select'), ('radio', 'Radio buttons'), ('date', 'Date'), ('datetime', 'Date/time'), ('hidden', 'Hidden field'), ('image', 'Image file'), ('document', 'Document file'), ('multiplechoicetypeahead', 'Multiple Choice (typeahead)')], max_length=255, verbose_name='field type'),
        ),
    ]
