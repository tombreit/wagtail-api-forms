import json

from django.db.models import Q

from wagtail.models import Site

from rest_framework import pagination
from rest_framework import serializers, generics, permissions
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from .models import CustomFormSubmission, TokenForm


class FormSubmissionSerializer(serializers.HyperlinkedModelSerializer):
    form_page_slug = serializers.SlugField(source='page.slug')
    form_page_title = serializers.SerializerMethodField(source='get_form_page_title')
    form_page_url = serializers.SerializerMethodField(source='get_form_page_url')
    form_data_api = serializers.SerializerMethodField(source='get_form_data_api')

    def get_form_page_title(self, obj):
        return obj.page.title

    def get_form_page_url(self, obj):
        current_site = Site.objects.first()
        return f"{current_site.root_url}{obj.page.url}"

    @staticmethod
    def _detele_key_from_dict(dictionary):
        # TODO: There should be only dicts, but sometimes I got '['
        if isinstance(dictionary, dict):
            valid_keys = [
                'label',
                'name',
                'type',
                'field_type',
                'type',
                'value',
            ]

            unwanted = set(dictionary) - set(valid_keys)
            for unwanted_key in unwanted: del dictionary[unwanted_key]

            if "type" in dictionary:
                dictionary["field_type"] = dictionary.pop("type")

        return dictionary

    def get_form_data_api(self, obj):
        form_data = json.loads(obj.form_data_api)
        form_data = map(self._detele_key_from_dict, form_data)
        return form_data

    class Meta:
        model = CustomFormSubmission
        lookup_field = 'id'
        fields = [
            'id',
            # 'submission_id',
            'form_page_title',
            'form_page_url',
            'form_page_slug',
            'submit_time',
            'form_data_api',
        ]


class FormSubmissionList(generics.ListAPIView):
    serializer_class = FormSubmissionSerializer
    lookup_field = 'id'

    authentication_classes = [
        SessionAuthentication,
        TokenAuthentication,
    ]
    permission_classes = [
        permissions.IsAuthenticated,
        # permissions.IsAdminUser,
        # IsSuperuserPermission,
        # IsOwnerOrReadOnly,
    ]

    def get_queryset(self):
        request_user = self.request.user
        force_empty_qs = True
        filter_expr = Q()

        # print(f"{request_user=}")
        # print(f"{request_user.auth_token=}")

        if request_user.is_superuser:
            # allow all
            force_empty_qs = False
            filter_expr = Q()
        elif hasattr(request_user, "auth_token"):
            # print(f"Filtering by token from request")
            force_empty_qs = False
            request_user_api_key = request_user.auth_token.key
            filter_expr = Q(api_user__key=request_user_api_key)

        qs = CustomFormSubmission.objects.none()
        if not force_empty_qs:
            # Get all FormPages the request with that token key are allowed:
            fps = (
                TokenForm
                .objects
                .filter(filter_expr)
                .values_list("form__pk", flat=True)
            )

            # Filter FormSubmissions to only expose submissions for requested form pages:
            qs = (
                CustomFormSubmission
                .objects
                .filter(page__pk__in=fps)
                .order_by('-submit_time')
            )

        return qs


class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 20


class FormSubmissionApi(FormSubmissionList):
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]
