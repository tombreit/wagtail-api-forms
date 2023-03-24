from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from wagtail.contrib.forms.views import SubmissionsListView
from private_storage.views import PrivateStorageDetailView

from wagtail_api_forms.settings.base import USE_ANTIVIR_SERVICE

from .validators import validate_ip_whitelisted
from .models import Attachment


class AttachmentDownloadView(PrivateStorageDetailView):
    model = Attachment
    model_file_field = 'file'

    def get_object(self):
        # see: https://github.com/edoburu/django-private-storage/issues/50
        return get_object_or_404(self.model, file=self.kwargs['path'])

    def can_access_file(self, private_file):
        can_access_file = False
        condition_authenticated_request = private_file.request.user.is_authenticated
        condition_viruschecked = self.object.av_passed if settings.USE_ANTIVIR_SERVICE else True
        condition_whitelisted_ip = validate_ip_whitelisted(private_file.request, settings.WHITELIST_IPS_ATTACHMENT_REQUEST)

        # Filter out all requests which do not pass our tests/checks/conditions:
        if not condition_viruschecked:
            raise PermissionDenied("Suspicious file data. Access denied.")
       
        if any([condition_whitelisted_ip, condition_authenticated_request]):
            can_access_file = True
        else:
            raise PermissionDenied("Not authenticated or whitelisted request. Access denied.")

        return can_access_file


class CustomSubmissionsListView(SubmissionsListView):
    orderable_fields = ('id', 'submit_time', 'client_ip', 'referrer')
