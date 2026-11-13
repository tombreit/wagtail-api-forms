"""
Customized wagtail form builder.

Added:
* image upload field
* document upload field
  See: https://dev.to/lb/image-uploads-in-wagtail-forms-39pl
* API for form submissions
* multi-step forms: page breaks split a form into steps, see steps.py
* the admin only shows the attributes of a form field that apply to its type
* after submitting, visitors are redirected to a thank-you page, which can show
  the poll results of the choice questions, see results.py
"""

import logging
import uuid
import datetime
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.http import Http404, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.cache import add_never_cache_headers
from django.utils.decorators import method_decorator
from django.utils.formats import date_format
from django.views.decorators.csp import csp_override

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
from wagtail.url_routing import RouteResult

from wagtail.contrib.forms.models import (
    AbstractEmailForm,
    AbstractFormField,
    AbstractForm,
    AbstractFormSubmission,
)
from wagtail.contrib.forms.panels import FormSubmissionsPanel

from .constants import (
    CHOICE_FIELD_TYPES,
    FIELD_TYPE_CHOICES,
    FILE_FIELD_TYPES,
    INPUT_FIELD_TYPES,
    PAGE_BREAK,
    PLACEHOLDER_FIELD_TYPES,
    FileArtChoices,
)
from .forms import CustomFormBuilder, CustomFormPageForm
from .model_mixins import FormPageApiMixin, FormPageAdditionalFieldsMixin
from .panels import FieldTypePanel
from .results import get_results
from .steps import bind_steps, split_into_steps

logger = logging.getLogger(__name__)


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
        # Schedule an AV scan only on initial create. Subsequent saves come
        # from the scan task itself (via Attachment.objects.update, not save),
        # but guarding here prevents accidental re-scan loops if a future
        # code path calls save() again.
        from .tasks import schedule_virusscan

        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            logger.info("Attachment %s: scheduling virus scan", self.id)
            schedule_virusscan(self.id)


def default_document_file_types():
    """Default for FormPage.allowed_document_file_types.

    Module-level callable so Django serializes the default by reference
    in migrations (stable across .env values) instead of baking in the
    resolved string at class-definition time.
    """
    return ", ".join(settings.FORMBUILDER_ALLOWED_DOCUMENT_FILE_TYPES)


class TokenUserProxy(Token):
    class Meta:
        proxy = True

    def __str__(self):
        return f"{self.user}: {self.key}"


# Sub-URLs of a form page: the step validation of multi-step forms, and the
# page visitors are redirected to after submitting
STEP_VALIDATION_PATH = "validate-step"
THANK_YOU_PATH = "thank-you"
# How long after submitting the thank-you page can be opened, e.g. reloaded.
# Not for the whole session: on a shared computer, the next person could open
# it, and see the poll answers of the previous one.
THANK_YOU_MAX_AGE = datetime.timedelta(minutes=30)


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
        help_text="A standalone heading displayed above this field. "
        "For page breaks: the heading of the new step.",
    )
    # Page breaks have no label, see clean()
    label = models.CharField(
        verbose_name=_("label"),
        max_length=255,
        blank=True,
        help_text=_("The label of the form field"),
    )

    field_type = models.CharField(
        verbose_name="field type",
        max_length=255,
        choices=FIELD_TYPE_CHOICES,
    )

    # Each attribute is only shown for the field types it applies to (see
    # FieldTypePanel), always in the same order: the field type, the required
    # attributes, the common ones, then those specific to some field types
    panels = [
        FieldPanel("field_type", required_on_save=True),
        # Required
        FieldTypePanel("label", INPUT_FIELD_TYPES),
        # Common
        FieldTypePanel(
            "help_text", [t for t in INPUT_FIELD_TYPES if t != "hidden"]
        ),
        FieldTypePanel("required", INPUT_FIELD_TYPES),
        FieldPanel("heading"),
        FieldTypePanel("css_classes", INPUT_FIELD_TYPES),
        # Specific
        FieldTypePanel("choices", CHOICE_FIELD_TYPES),
        # A default value of an upload field would be taken as the upload
        FieldTypePanel(
            "default_value",
            [t for t in INPUT_FIELD_TYPES if t not in FILE_FIELD_TYPES],
        ),
        FieldTypePanel("placeholder", PLACEHOLDER_FIELD_TYPES),
    ]

    page = ParentalKey("FormPage", on_delete=models.CASCADE, related_name="form_fields")

    def clean(self):
        super().clean()
        if self.field_type != PAGE_BREAK and not self.label:
            raise ValidationError({"label": _("This field is required.")})

    def get_field_clean_name(self):
        if self.field_type == PAGE_BREAK:
            # Page breaks have no label and hold no answers: their name only
            # has to be unique
            return f"page_break_{uuid.uuid4().hex[:8]}"
        return super().get_field_clean_name()

    def save(self, *args, **kwargs):
        """
        Ensure clean_name is always populated. Upstream only sets it on first
        creation (pk is None), so if it ever gets wiped (e.g. revision restore
        edge case) it would stay empty forever — breaking submissions.
        We intentionally do NOT regenerate on every save, as that would
        invalidate historical submission data when a label is renamed.
        """
        if not self.clean_name:
            self.clean_name = self.get_field_clean_name()
        if not self.clean_name:
            raise ValidationError(
                {
                    "label": "Field label must produce a valid field name (avoid using only special characters)."
                }
            )
        super().save(*args, **kwargs)


class FormPage(FormPageApiMixin, FormPageAdditionalFieldsMixin, AbstractEmailForm):
    base_form_class = CustomFormPageForm

    parent_page_types = ["home.ContainerPage"]
    subpage_types = []

    intro = RichTextField(
        blank=True, verbose_name="Intro text", help_text="Displayed above the form."
    )
    outro = RichTextField(
        blank=True,
        verbose_name="Outro text",
        help_text="Displayed below the form, but before the “Submit” button.",
    )
    thank_you_text = RichTextField(
        blank=True, help_text="Displayed after the form has been submitted."
    )
    show_results = models.BooleanField(
        default=False,
        verbose_name="Show poll results after submitting",
        help_text="After submitting, show how often each choice of the radio "
        "button, drop down, checkboxes and multiple select questions was "
        "chosen. Answers to other questions are never shown.",
    )
    use_captcha = models.BooleanField(default=False)
    allowed_document_file_types = models.CharField(
        max_length=255,
        default=default_document_file_types,
        help_text=(
            "Comma separated list of allowed file extensions for document uploads. "
            "Each one needs its leading dot. E.g. '.pdf, .docx'."
        ),
    )

    settings_panels = AbstractForm.settings_panels + [
        FieldPanel("use_captcha"),
        FieldPanel("allowed_document_file_types", permission="superuser"),
    ]

    content_panels = AbstractEmailForm.content_panels + [
        FormSubmissionsPanel(),
        FieldPanel("intro", classname="full"),
        HelpPanel(
            content='Some more information in our <a href="/docs/">docs</a>.',
        ),
        InlinePanel(
            "form_fields",
            label="Form fields",
            attrs={
                # w-rules shows/hides the attributes of the form fields (see
                # FieldTypePanel), waf-form-fields titles and collapses them
                # (see static/formpages/admin/form-fields.js)
                "data-controller": "w-rules waf-form-fields",
                "data-action": "change->w-rules#resolve "
                "input->waf-form-fields#update change->waf-form-fields#update",
                "data-waf-form-fields-page-break-value": PAGE_BREAK,
                "data-waf-form-fields-step-label-value": _("Step %(number)s"),
            },
        ),
        FieldPanel("outro", classname="full"),
        MultiFieldPanel(
            [
                FieldPanel("thank_you_text", classname="full"),
                FieldPanel("show_results"),
            ],
            "After submitting",
        ),
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

    def get_form_fields(self):
        """
        The questions of the form, without page breaks. Used for the form, the
        columns of the submissions list and export, the API data and the email.
        """
        return [
            form_field
            for form_field in self.form_fields.all()
            if form_field.field_type != PAGE_BREAK
        ]

    def get_steps(self):
        """The steps of the form: one, unless it has page breaks."""
        return split_into_steps(self.form_fields.all())

    def get_step_context(self, request, form):
        """The template context of a multi-step form; empty for other forms."""
        steps = self.get_steps()
        if len(steps) < 2:
            return {}

        form_steps = bind_steps(steps, form)
        if getattr(request, "is_preview", False):
            # Unpublished pages have no URL: the preview shows the steps
            # without validating them
            step_validation_url = ""
        else:
            step_validation_url = f"{self.get_url(request)}{STEP_VALIDATION_PATH}/"
        return {
            "form_steps": form_steps,
            # After an invalid submission: the first step with errors
            "initial_step": next(
                (step.number for step in form_steps if step.has_errors), 1
            ),
            "step_validation_url": step_validation_url,
        }

    def get_preview_context(self, request, mode_name):
        context = super().get_preview_context(request, mode_name)
        context.update(self.get_step_context(request, context["form"]))
        return context

    def route(self, request, path_components):
        if self.live and path_components == [STEP_VALIDATION_PATH]:
            return RouteResult(self, kwargs={"validate_step": True})
        if self.live and path_components == [THANK_YOU_PATH]:
            return RouteResult(self, kwargs={"thank_you": True})
        return super().route(request, path_components)

    def get_url_with_embed(self, request, path=""):
        """The URL of the page or of a sub-URL, staying in embed mode."""
        url = f"{self.get_url(request)}{path}"
        return f"{url}?embed=true" if request.GET.get("embed") else url

    def get_session_key(self):
        """Holds the submission of the visitor, for the thank-you page."""
        return f"formpage-{self.pk}-submission"

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
        Called after a submission has been stored: redirect to the thank-you
        page, so reloading it doesn't submit the form again.
        """
        if form_submission is None:
            # The admin preview of the landing page
            return self.render_thank_you(request)

        if not request.user.is_authenticated:
            # A session key planted by another site of the same domain would
            # let that site open the thank-you page. Logged-in users have got
            # a new key when logging in; keep theirs for their other tabs.
            request.session.cycle_key()
        request.session[self.get_session_key()] = str(form_submission.pk)
        return redirect(self.get_url_with_embed(request, f"{THANK_YOU_PATH}/"))

    def serve_thank_you(self, request):
        """
        Only the visitor who has submitted the form sees the thank-you page,
        and only for a while.
        """
        session_key = self.get_session_key()
        submission_id = request.session.get(session_key)
        form_submission = (
            self.get_submissions().filter(pk=submission_id).first()
            if submission_id
            else None
        )
        if (
            form_submission is None
            or timezone.now() - form_submission.submit_time > THANK_YOU_MAX_AGE
        ):
            request.session.pop(session_key, None)
            return redirect(self.get_url_with_embed(request))
        return self.render_thank_you(request, form_submission)

    def render_thank_you(self, request, form_submission=None):
        context = self.get_context(request)
        context["form_submission"] = form_submission
        # Embed mode: the embedding page scrolls to the thank-you text
        context["ctx_submitted"] = True
        if self.show_results:
            context["results"] = get_results(self, form_submission)
        response = TemplateResponse(
            request, self.get_landing_page_template(request), context
        )
        # Personal: it depends on the session, and marks the visitor's answers
        add_never_cache_headers(response)
        return response

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

    @method_decorator(csp_override(settings.FORMBUILDER_FORMPAGE_CSP))
    def serve(self, request, *args, validate_step=False, thank_you=False, **kwargs):
        if validate_step:
            return self.serve_step_validation(request)
        if thank_you:
            return self.serve_thank_you(request)

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
        context.update(self.get_step_context(request, form))

        return TemplateResponse(request, self.get_template(request), context)

    def serve_step_validation(self, request):
        """
        Validate one step of a multi-step form, so the browser can show its
        errors before moving on to the next step. Nothing is stored: the form
        is submitted at the end with the answers of all steps, as usual.
        """
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

        steps = self.get_steps()
        if len(steps) < 2:
            raise Http404

        try:
            step_number = int(request.POST.get("form_step", ""))
        except ValueError:
            step_number = 1
        step = steps[min(max(step_number, 1), len(steps)) - 1]

        form_class = self.form_builder(step.fields).get_form_class()
        # The captcha is only checked when the form is submitted: checking it
        # uses up the answer
        form_class.base_fields.pop(CustomFormBuilder.CAPTCHA_FIELD_NAME, None)
        form = form_class(
            request.POST,
            request.FILES,
            page=self,
            user=request.user,
            **self.get_form_parameters(),
        )
        is_valid = form.is_valid()
        return JsonResponse({"valid": is_valid, "errors": form.errors.get_json_data()})


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
