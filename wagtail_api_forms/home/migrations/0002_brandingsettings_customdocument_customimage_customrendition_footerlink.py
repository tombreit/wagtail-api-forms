# Generated by Django 3.2.9 on 2021-11-28 22:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import taggit.managers
import uuid
import wagtail.models.collections
import wagtail.images.models
import wagtail.search.index
import wagtail_api_forms.home.models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0066_collection_management_permissions'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('taggit', '0003_taggeditem_add_unique_index'),
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('file', models.ImageField(height_field='height', upload_to=wagtail.images.models.get_upload_to, verbose_name='file', width_field='width')),
                ('width', models.IntegerField(editable=False, verbose_name='width')),
                ('height', models.IntegerField(editable=False, verbose_name='height')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                ('focal_point_x', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_y', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_width', models.PositiveIntegerField(blank=True, null=True)),
                ('focal_point_height', models.PositiveIntegerField(blank=True, null=True)),
                ('file_size', models.PositiveIntegerField(editable=False, null=True)),
                ('file_hash', models.CharField(blank=True, editable=False, max_length=40)),
                ('collection', models.ForeignKey(default=wagtail.models.collections.get_root_collection_id, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.collection', verbose_name='collection')),
                ('tags', taggit.managers.TaggableManager(blank=True, help_text=None, through='taggit.TaggedItem', to='taggit.Tag', verbose_name='tags')),
                ('uploaded_by_user', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='uploaded by user')),
            ],
            options={
                'abstract': False,
            },
            bases=(wagtail.images.models.ImageFileMixin, wagtail.search.index.Indexed, models.Model),
        ),
        migrations.CreateModel(
            name='CustomDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('file_size', models.PositiveIntegerField(editable=False, null=True)),
                ('file_hash', models.CharField(blank=True, editable=False, max_length=40)),
                ('file', models.FileField(upload_to=wagtail_api_forms.home.models.add_uuid_prefix, verbose_name='file')),
                ('collection', models.ForeignKey(default=wagtail.models.collections.get_root_collection_id, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.collection', verbose_name='collection')),
                ('tags', taggit.managers.TaggableManager(blank=True, help_text=None, through='taggit.TaggedItem', to='taggit.Tag', verbose_name='tags')),
                ('uploaded_by_user', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='uploaded by user')),
            ],
            options={
                'verbose_name': 'document',
                'verbose_name_plural': 'documents',
                'abstract': False,
            },
            bases=(wagtail.search.index.Indexed, models.Model),
        ),
        migrations.CreateModel(
            name='FooterLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('title', models.CharField(max_length=255)),
                ('external_url', models.URLField(blank=True, verbose_name='External link')),
                ('internal_page', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailcore.page')),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale')),
            ],
            options={
                'abstract': False,
                'unique_together': {('translation_key', 'locale')},
            },
        ),
        migrations.CreateModel(
            name='CustomRendition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filter_spec', models.CharField(db_index=True, max_length=255)),
                ('file', models.ImageField(height_field='height', upload_to=wagtail.images.models.get_rendition_upload_to, width_field='width')),
                ('width', models.IntegerField(editable=False)),
                ('height', models.IntegerField(editable=False)),
                ('focal_point_key', models.CharField(blank=True, default='', editable=False, max_length=16)),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='renditions', to='home.customimage')),
            ],
            options={
                'unique_together': {('image', 'filter_spec', 'focal_point_key')},
            },
            bases=(wagtail.images.models.ImageFileMixin, models.Model),
        ),
        migrations.CreateModel(
            name='BrandingSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('brand_name_en', models.CharField(default='A Company that Makes Everything', help_text='Company, institute, site name (english version).', max_length=255, verbose_name='Name (EN)')),
                ('brand_name_de', models.CharField(default='A Company that Makes Everything', help_text='Company, institute, site name (german version).', max_length=255, verbose_name='Name (DE)')),
                ('brand_abbr', models.CharField(default='ACME', help_text='Company, institute, site abbreviation.', max_length=255, verbose_name='Abbreviation')),
                ('brand_logo_en', models.FileField(blank=True, help_text='Logo file (english version). Format: SVG.', null=True, upload_to='branding/', validators=[wagtail_api_forms.home.models.validate_logo_image_file_extension], verbose_name='Logo file (EN)')),
                ('brand_logo_de', models.FileField(blank=True, help_text='Logo file (german version). Format: SVG.', null=True, upload_to='branding/', validators=[wagtail_api_forms.home.models.validate_logo_image_file_extension], verbose_name='Logo file (DE)')),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale')),
                ('site', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, to='wagtailcore.site')),
            ],
            options={
                'abstract': False,
                'unique_together': {('translation_key', 'locale')},
            },
        ),
    ]
