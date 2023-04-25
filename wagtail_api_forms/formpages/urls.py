from django.urls import path, re_path, include

from .views import AttachmentDownloadView
from .api import FormSubmissionApi


urlpatterns_captcha = [
    path('', include('captcha.urls')),
]

urlpatterns_api = [
    path('v2/', FormSubmissionApi.as_view()),  # paginated
    # path('formsubmissions/<uuid:id>/', FormSubmissionDetail.as_view()),
]

urlpatterns_securedownload = [
    re_path('(?P<path>.*)$', AttachmentDownloadView.as_view(), name='serve_private_file'),
]
