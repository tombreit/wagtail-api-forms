from django.conf import settings
from django.forms import DateField, DateTimeField, MultipleChoiceField, widgets
from django.utils.text import camel_case_to_spaces, slugify

from wagtail.contrib.forms.forms import FormBuilder
from captcha.fields import CaptchaField

from .fields import FormBuilderBaseFileField
from .constants import FileArtChoices


class CustomFormBuilder(FormBuilder):
    CAPTCHA_FIELD_NAME = "wagtailcaptcha"

    def create_date_field(self, field, options):
        return DateField(
            widget=widgets.DateInput(attrs={"type": "date"}),
            **options,
        )

    def create_datetime_field(self, field, options):
        return DateTimeField(
            widget=widgets.DateTimeInput(attrs={"type": "datetime-local"}),
            **options,
        )

    def create_image_field(self, field, options):
        field = FormBuilderBaseFileField(
            # Fixme: ClearableFileInput does not show up in rendered page
            # widget=forms.ClearableFileInput,
            allowed_file_types=settings.FORMBUILDER_ALLOWED_IMAGE_FILE_TYPES,
            file_art=FileArtChoices.IMAGE_FILE,
            **options,
        )
        return field

    def create_document_field(self, field, options):
        field = FormBuilderBaseFileField(
            # Fixme: ClearableFileInput does not show up in rendered page
            # widget=forms.ClearableFileInput,
            allowed_file_types=settings.FORMBUILDER_ALLOWED_DOCUMENT_FILE_TYPES,
            file_art=FileArtChoices.DOCUMENT_FILE,
            **options,
        )
        return field

    def create_multiplechoicetypeahead_field(self, field, options):
        options["choices"] = self.get_formatted_field_choices(field)

        return MultipleChoiceField(
            widget=widgets.SelectMultiple(
                attrs={
                    "class": "is-tom-select",
                }
            ),
            **options,
        )

    # def get_field_options(self, field):
    #     """
    #     Extend field options to include custom css classes.
    #     Fixme: do not know how to update option['widget']['attrs'] for all fields.
    #     """
    #     options = super().get_field_options(field)
    #     return options

    def get_create_field_function(self, type):
        """
        Override the method to prepare a wrapped function that will call the original
        function (which returns a field) and update the widget's attrs with a custom
        value that can be used within the template when rendering each field.
        https://stackoverflow.com/a/68920368/5071435
        """

        create_field_function = super().get_create_field_function(type)

        def wrapped_create_field_function(field, options):
            created_field = create_field_function(field, options)

            widget_classname = created_field.widget.__class__.__name__
            widget_classname = slugify(camel_case_to_spaces(widget_classname))
            widget_classname = f"widget-class-{widget_classname}"

            created_field.widget.attrs.update(
                {
                    "css_classes": f"{field.css_classes} {widget_classname}",
                    "placeholder": field.placeholder,
                    "heading": field.heading,
                }
            )
            return created_field

        return wrapped_create_field_function

    @property
    def formfields(self):
        # Add wagtailcaptcha to formfields property
        fields = super().formfields
        fields[self.CAPTCHA_FIELD_NAME] = CaptchaField(
            label="Captcha. Add one to each digit. 9 becomes 0."
        )
        return fields


def remove_captcha_field(form):
    form.fields.pop(CustomFormBuilder.CAPTCHA_FIELD_NAME, None)
    form.cleaned_data.pop(CustomFormBuilder.CAPTCHA_FIELD_NAME, None)
