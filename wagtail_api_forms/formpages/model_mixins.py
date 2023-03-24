import json

from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext_lazy as _
from django import forms

from wagtail.models import Site

from .constants import FileArtChoices
from .forms import CustomFormBuilder, remove_captcha_field


class FormPageApiMixin(object):
    def get_field_definitions(self):
        """Build api data dict."""
        field_definitions = []
        for field in self.get_form_fields():
            field_dict = {
                "label": field.label,
                "name": field.clean_name,
                "field_type": field.field_type,
                # "default_value": field.default_value,
                # "required": field.required,
                # "help_text": field.help_text,
                # "choices": field.choices,
            }
            field_definitions.append(field_dict)

        return field_definitions

    def get_form_data_for_api(self, cleaned_form_data):
        form_data_api = []
        field_definitions = self.get_field_definitions()

        for key, value in cleaned_form_data.items():
            # Check if dict with the current key exists in list of dicts and return matched dict:
            # Caution: key 'name' must match item in get_field_definitions()!
            res = next((item for item in field_definitions if item["name"] == key), False)
            if res:
                res.update({"value": value})
                
            form_data_api.append(res)

        return json.dumps(form_data_api, cls=DjangoJSONEncoder)


class FormPageAdditionalFieldsMixin(object):

    form_builder = CustomFormBuilder

    def get_submission_class(self):
        from .models import CustomFormSubmission
        return CustomFormSubmission

    def process_form_submission(self, form, client_ip, referrer):
        """
        Processes the form submission, if an Image upload is found, pull out the
        files data, create an actual Wagtail Image and reference its ID only in the
        stored form response.
        """

        from .models import Attachment

        remove_captcha_field(form)

        cleaned_data = form.cleaned_data
        attachment_ids = []

        for name, field in form.fields.items():

            if isinstance(field, forms.FileField):
                _current_site = Site.objects.first()

                if field.file_art is FileArtChoices.IMAGE_FILE or field.file_art is FileArtChoices.DOCUMENT_FILE:
                    file_data = cleaned_data[name]
                    if file_data:
                        kwargs = {
                            'file': cleaned_data[name],
                            'file_art': field.file_art,
                        }
                        attachment = Attachment(**kwargs)
                        attachment.save()
                        attachment_link = f"{_current_site.root_url}{attachment.file.url}"
                        cleaned_data.update({name: attachment_link})

                        attachment_ids.append(attachment.id)
                    # else:
                    #     del cleaned_data[name]

        submission = self.get_submission_class().objects.create(
            # https://docs.wagtail.org/en/stable/releases/3.0.html#replaced-form-data-textfield-with-jsonfield-in-abstractformsubmission
            # form_data=json.dumps(cleaned_data, cls=DjangoJSONEncoder),
            form_data=cleaned_data,
            page=self,
            form_data_api=self.get_form_data_for_api(cleaned_data),
            client_ip=client_ip,
            referrer=referrer,
        )

        if attachment_ids:
            # Explictly set form_submission obj for every attachment
            Attachment.objects.filter(id__in=attachment_ids).update(
                form_submission=submission
            )

        # important: if extending AbstractEmailForm, email logic must be re-added here
        if self.to_address:
            self.send_mail(form)

        return submission

