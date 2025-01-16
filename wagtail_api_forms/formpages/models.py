"""
Customized wagtail form builder.

Added:
* image upload field
* document upload field
  See: https://dev.to/lb/image-uploads-in-wagtail-forms-39pl
* API for form submissions
"""

import uuid
import datetime
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.template.response import TemplateResponse
from django.utils.formats import date_format

from private_storage.fields import PrivateFileField
from rest_framework.authtoken.models import Token
from modelcluster.fields import ParentalKey
from ipware import get_client_ip

from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
    HelpPanel,
)
from wagtail.fields import RichTextField

from wagtail.contrib.forms.models import (
    AbstractEmailForm,
    AbstractFormField,
    AbstractForm,
    AbstractFormSubmission,
    FORM_FIELD_CHOICES,
)
from wagtail.contrib.forms.panels import FormSubmissionsPanel

from .constants import FileArtChoices
from .forms import CustomFormBuilder
from .model_mixins import FormPageApiMixin, FormPageAdditionalFieldsMixin


def attachment_directory_path(instance, filename):
    """
    File will be uploaded to MEDIA_ROOT/attachments/<uuid>__<filename>
    The root directory 'attachments' in media is set via settings.base
    PRIVATE_STORAGE_ROOT and therefore we only create the bare filename here.
    """

    return "{uuid}__{basename}{suffix}".format(
        uuid=uuid.uuid4(),
        basename=slugify(Path(filename).stem),
        suffix=Path(filename).suffix,  # the dot is included in the suffix
    )


class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = PrivateFileField(
        upload_to=attachment_directory_path,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    form_submission = models.ForeignKey(
        "CustomFormSubmission",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    av_scanned_at = models.DateTimeField(blank=True, null=True)
    av_passed = models.BooleanField(default=False)
    av_reason = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    file_art = models.CharField(
        max_length=8,
        choices=FileArtChoices.choices,
        default=FileArtChoices.DOCUMENT_FILE,
    )

    def save(self, *args, **kwargs):
        from .tasks import schedule_virusscan

        """
        Todo: Re-think/re-implement this logic!

        If is new instance:
          1. save instance to get the instance id
          2. run virusscan
          3. update instance virusscan-related fields
        
        If instance already exists and save() is triggered:
          1. run virusscan
          2. update instance virusscan-related fields
        """

        # created = self._state.adding
        # if created:
        #     print("Attachment instance created, calling super().save()...")
        #     super().save()

        # print(f"Attachment instance {self.id}: trigger schedule_virusscan...")
        # _scan = schedule_virusscan(self.id)
        # # _scan.get(blocking=True)
        # return

        super().save()
        print(f"Attachment instance {self.id}: trigger schedule_virusscan...")
        scan = schedule_virusscan(self.id)
        # scan.get()


class TokenUserProxy(Token):
    class Meta:
        proxy = True

    def __str__(self):
        return f"{self.user}: {self.key}"


class UserFormField(AbstractFormField):
    css_classes = models.CharField(
        blank=True,
        max_length=255,
        verbose_name="CSS class names",
        help_text="Additional CSS classes, space separated. See docs for usage hints.",
    )
    placeholder = models.CharField(
        "Placeholder",
        max_length=254,
        blank=True,
        help_text="This short placeholder is displayed in the input field before the user enters a value.",
    )
    help_text = RichTextField(
        verbose_name=_("help text"),
        blank=True,
    )
    heading = models.CharField(
        "Heading",
        max_length=254,
        blank=True,
        help_text="A standalone heading displayed above this field.",
    )

    field_type = models.CharField(
        verbose_name="field type",
        max_length=255,
        choices=list(FORM_FIELD_CHOICES)
        + [
            ("image", _("Image file")),
            ("document", _("Document file")),
            ("multiplechoicetypeahead", _("Multiple Choice (typeahead)")),
            # ('image64', 'Uploaded Image (base64)'),
        ],
    )

    panels = AbstractFormField.panels + [
        FieldPanel("placeholder"),
        FieldPanel("heading"),
        FieldPanel("css_classes"),
    ]

    page = ParentalKey("FormPage", on_delete=models.CASCADE, related_name="form_fields")

    # This customization invalidated old field names after renameing a
    # field. Using the standard save method prevents this.c
    # def save(self, *args, **kwargs):
    #     """
    #     Set clean_name on each save to the corresponding clean_name of the label field.
    #     Upstream only sets clean_name once, when the first instance is created.
    #     """
    #     clean_name = get_field_clean_name(self.label)
    #     self.clean_name = clean_name
    #     super().save(*args, **kwargs)


class FormPage(FormPageApiMixin, FormPageAdditionalFieldsMixin, AbstractEmailForm):
    parent_page_types = ["home.ContainerPage"]
    subpage_types = []

    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)
    use_captcha = models.BooleanField(default=False)

    settings_panels = AbstractForm.settings_panels + [
        FieldPanel("use_captcha"),
    ]

    content_panels = AbstractEmailForm.content_panels + [
        FormSubmissionsPanel(),
        FieldPanel("intro", classname="full"),
        HelpPanel(
            content='Some more information in our <a href="/docs/">docs</a>.',
        ),
        InlinePanel("form_fields", label="Form fields"),
        FieldPanel("thank_you_text", classname="full"),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("from_address", classname="col6"),
                        FieldPanel("to_address", classname="col6"),
                    ]
                ),
                FieldPanel("subject"),
            ],
            "Email",
        ),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context["ctx_embed"] = "true" if request.GET.get("embed") else ""
        return context

    def get_form_class(self):
        """
        Captcha only when activated for this form.
        https://github.com/wagtail/wagtail/blob/main/wagtail/contrib/forms/models.py#L225
        """
        fb = self.form_builder(self.get_form_fields())
        fb = fb.get_form_class()

        if not self.use_captcha:
            fb.base_fields.pop(CustomFormBuilder.CAPTCHA_FIELD_NAME, None)

        return fb

    def get_submissions_list_view_class(self):
        from .views import CustomSubmissionsListView

        return CustomSubmissionsListView

    def get_data_fields(self):
        data_fields = super().get_data_fields()

        data_fields += [
            ("client_ip", _("IP")),
            ("referrer", _("Referrer")),
        ]

        return data_fields

    def __str__(self):
        return f"{self.title} ({self.locale.language_code.upper()})"

    def render_landing_page(self, request, form_submission=None, *args, **kwargs):
        """
        Renders the landing page.
        You can override this method to return a different HttpResponse as
        landing page. E.g. you could return a redirect to a separate page.
        """
        context = self.get_context(request)
        context.update(
            {
                "form_submission": form_submission,
            }
        )

        return TemplateResponse(
            request, self.get_landing_page_template(request), context
        )

    def render_email(self, form):
        # To get custom date formats we need to subclass render_email method
        # https://github.com/wagtail/wagtail/blob/01c250859a4db69a58bdd16ec633e4f96d408b48/wagtail/contrib/forms/models.py#L342
        # Get the original content (string)
        # email_content = super().render_email(form)

        content = []

        cleaned_data = form.cleaned_data
        for field in form:
            if field.name not in cleaned_data:
                continue

            value = cleaned_data.get(field.name)

            if isinstance(value, list):
                value = ", ".join(value)

            if isinstance(value, datetime.datetime):
                value = date_format(value, settings.FORMBUILDER_EMAIL_DATETIME_FORMAT)
            elif isinstance(value, datetime.date):
                value = date_format(value, settings.FORMBUILDER_EMAIL_DATE_FORMAT)

            content.append("{}: {}".format(field.label, value))

        body_content = "\n".join(content)

        _separator = 71 * "-"

        content = [
            f"Form title:    {self.title}",
            f"Submitted via: {self.full_url}",
            f"Submitted on:  {datetime.datetime.now():%Y-%m-%d %H:%M:%S}",
            "",
            "Form data:",
            _separator,
            "",
            body_content,
            "",
            _separator,
        ]

        # Content is joined with a new line to separate each text line
        content = "\n".join(content)

        return content

    def serve(self, request, *args, **kwargs):
        if request.method == "POST":
            referrer = request.META.get("HTTP_REFERER", "")
            client_ip, _ = get_client_ip(request)

            form = self.get_form(
                request.POST,
                request.FILES,
                page=self,
                user=request.user,
            )

            if form.is_valid():
                form_submission = self.process_form_submission(
                    form, client_ip, referrer
                )
                return self.render_landing_page(
                    request, form_submission, *args, **kwargs
                )
        else:
            form = self.get_form(page=self, user=request.user)

        context = self.get_context(request)
        context.update(
            {
                "form": form,
            }
        )

        return TemplateResponse(request, self.get_template(request), context)


class TokenForm(models.Model):
    form = models.ForeignKey(
        FormPage,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    api_user = models.ForeignKey(
        TokenUserProxy,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f"{self.form} <-> {self.api_user}"

    class Meta:
        unique_together = ["form", "api_user"]


class CustomFormSubmission(AbstractFormSubmission):
    """Data for a Form submission."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form_data_api = models.TextField(blank=True)
    client_ip = models.GenericIPAddressField(blank=True, null=True)
    referrer = models.CharField(_("Referrer URL"), max_length=250, blank=True)

    def get_data(self):
        form_data = super().get_data()
        form_data.update(
            {
                "client_ip": self.client_ip,
                "referrer": self.referrer,
                "form_data_api": self.form_data_api,
            }
        )
        return form_data

    def __str__(self):
        return str(self.id)
