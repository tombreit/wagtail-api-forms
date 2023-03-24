from django.urls import path, re_path, include

from .views import AttachmentDownloadView
from .api import FormSubmissionList, FormSubmissionApi


urlpatterns_captcha = [
    path('', include('captcha.urls')),
]

urlpatterns_api = [
    path('v1/', FormSubmissionList.as_view()),
    path('v2/', FormSubmissionApi.as_view()),  # paginated
    # path('formsubmissions/<uuid:id>/', FormSubmissionDetail.as_view()),
]

urlpatterns_securedownload = [
    re_path('(?P<path>.*)$', AttachmentDownloadView.as_view(), name='serve_private_file'),
]
