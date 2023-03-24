import os.path
from pathlib import Path
from uuid import uuid4

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

from wagtail.models import Orderable, Page, TranslatableMixin
from wagtail.coreutils import string_to_ascii
from wagtail.images.models import Image, AbstractImage, AbstractRendition
from wagtail.documents.models import Document, AbstractDocument
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.admin.panels import (
    FieldPanel, InlinePanel, PageChooserPanel
)
from wagtail.snippets.models import register_snippet


from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.models import Page


def add_uuid_prefix(instance, filename):
    from wagtail_api_forms.home.models import CustomDocument

    prefixed_filename = f"{str(uuid4())}_{filename}"

    if isinstance(instance, CustomDocument):
        return f"documents/{prefixed_filename}"
    else:
        return prefixed_filename


def validate_logo_image_file_extension(value):
    valid_extensions = ["svg"]
    return FileExtensionValidator(allowed_extensions=valid_extensions)(value)


def validate_favicon_file_extension(value):
    valid_extensions = ["ico", "png"]
    return FileExtensionValidator(allowed_extensions=valid_extensions)(value)


def branding_logo_path(instance, filename):
    return '{uuid}__{basename}{suffix}'.format(
        uuid=uuid4(),
        basename=slugify(Path(filename).stem),
        suffix=Path(filename).suffix,  # the dot is included in the suffix
    )


@register_setting
class BrandingSettings(TranslatableMixin, BaseGenericSetting, ClusterableModel):
    brand_name_en = models.CharField(
        max_length=255,
        blank=False,
        verbose_name="Name (EN)",
        default=_("A Company that Makes Everything"),
        help_text=_("Company, institute, site name (english version)."),
    )
    brand_name_de = models.CharField(
        max_length=255,
        blank=False,
        verbose_name="Name (DE)",
        default=_("A Company that Makes Everything"),
        help_text=_("Company, institute, site name (german version)."),
    )
    brand_abbr = models.CharField(
        max_length=255,
        blank=False,
        verbose_name="Abbreviation",
        default="ACME",
        help_text=_("Company, institute, site abbreviation."),
    )
    brand_logo_en = models.FileField(
        null=True,
        blank=True,
        upload_to='branding/',
        validators=[validate_logo_image_file_extension],
        verbose_name="Logo file (EN)",
        help_text=_('Logo file (english version). Format: SVG.'),
    )
    brand_logo_de = models.FileField(
        null=True,
        blank=True,
        upload_to='branding/',
        validators=[validate_logo_image_file_extension],
        verbose_name="Logo file (DE)",
        help_text=_('Logo file (german version). Format: SVG.'),
    )
    brand_figurative_mark = models.FileField(
        null=True,
        blank=True,
        upload_to='branding/',
        validators=[validate_logo_image_file_extension],
        verbose_name="Figurative mark ('Bildmarke')",
        help_text=_('Figurative mark. Format: SVG.'),
    )
    favicon = models.FileField(
        null=True,
        blank=True,
        upload_to='branding/',
        validators=[validate_favicon_file_extension],
        verbose_name="Favicon file",
        help_text=_('Favicon file. Formats: ICO or PNG'),
    )

    panels = [
        FieldPanel('brand_abbr'),
        FieldPanel('brand_name_en'),
        FieldPanel('brand_logo_en'),
        FieldPanel('brand_name_de'),
        FieldPanel('brand_logo_de'),
        FieldPanel('brand_figurative_mark'),
        FieldPanel('favicon'),
    ]


@register_snippet
class FooterLinks(TranslatableMixin, ClusterableModel, models.Model):

    panels = [
        InlinePanel('footer_links', label="Footer links"),
    ]

    def __str__(self):
        links = self.footer_links.values_list('title', flat=True)
        return f"{', '.join(links)}"

    class Meta:
        verbose_name = "Footer links"
        verbose_name_plural = "Footer links"
        unique_together = ('translation_key', 'locale')


class FooterLink(models.Model):
    title = models.CharField(max_length=255)
    external_url = models.URLField(
        "External link",
        blank=True,
    )
    internal_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    @property
    def get_url(self):
        url = None
        if self.external_url:
            url = self.external_url
        elif self.internal_page:
            url = self.internal_page.url
        
        return url

    panels = [
        FieldPanel('title'),
        FieldPanel('external_url'),
        PageChooserPanel('internal_page'),
    ]

    def clean(self):
        if all([self.external_url, self.internal_page]):
            raise ValidationError(_('Choose external URL or Internal page, not both.'))
        if not any([self.external_url, self.internal_page]):
            raise ValidationError(_('You must set either External URL or Internal page.'))

    def __str__(self):
        return f"{self.title} → {self.get_url}"

    class Meta:
        abstract = True


class FooterLinksFooterLink(Orderable, FooterLink):
    page = ParentalKey('home.FooterLinks', on_delete=models.CASCADE, related_name='footer_links')


class HomePage(Page):
    subpage_types = ['home.ContainerPage']


class ContainerPage(Page):
    parent_page_types = ['home.HomePage']
    subpage_types = ['formpages.FormPage']


class CustomImage(AbstractImage):
    """
    https://docs.wagtail.io/en/stable/advanced_topics/images/custom_image_model.html
    """

    admin_form_fields = Image.admin_form_fields

    def get_upload_to(self, filename):
        """
        Upstream method at:
        https://github.com/wagtail/wagtail/blob/main/wagtail/images/models.py#L129
        Extended to prefix all files with an uuid4 string.
        """
        folder_name = 'original_images'
        # filename = f"{str(uuid4())}_{self.file.field.storage.get_valid_name(filename)}"
        filename = add_uuid_prefix(instance=None, filename=self.file.field.storage.get_valid_name(filename))

        # do a unidecode in the filename and then
        # replace non-ascii characters in filename with _ , to sidestep issues with filesystem encoding
        filename = "".join((i if ord(i) < 128 else '_') for i in string_to_ascii(filename))

        # Truncate filename so it fits in the 100 character limit
        # https://code.djangoproject.com/ticket/9893
        full_path = os.path.join(folder_name, filename)
        if len(full_path) >= 95:
            chars_to_trim = len(full_path) - 94
            prefix, extension = os.path.splitext(filename)
            filename = prefix[:-chars_to_trim] + extension
            full_path = os.path.join(folder_name, filename)

        return full_path


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(
        CustomImage,
        on_delete=models.CASCADE,
        related_name='renditions',
    )

    class Meta:
        unique_together = (
            ('image', 'filter_spec', 'focal_point_key'),
        )


class CustomDocument(AbstractDocument):
    file = models.FileField(
        upload_to=add_uuid_prefix,
        verbose_name=_('file'),
    )

    admin_form_fields = Document.admin_form_fields + (
        # Add all custom fields names to make them appear in the form:
        'file',
    )
