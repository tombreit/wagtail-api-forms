from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path
from django.contrib import admin

from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from wagtail_api_forms.formpages import urls as formpages_urls
# from sphinx_view import DocumentationView
# from wagtail_api_forms.home.views import sphinx_searchindex_view


urlpatterns = [
    path('attachments/', include(formpages_urls.urlpatterns_securedownload)),
    path('django-admin/', admin.site.urls),
    path('admin/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('api/formsubmission/', include(formpages_urls.urlpatterns_api)),
    path('captcha/', include(formpages_urls.urlpatterns_captcha)),
    # path('cspreports/', include('cspreports.urls')),

    # django_sphinx_view
    # path('docs/searchindex.js', sphinx_searchindex_view, name='sphinx_searchindex_view'),
    # path(
    #     "docs<path:path>",
    #     DocumentationView.as_view(
    #         json_build_dir=Path('docs/_build/json/'),
    #         base_template_name="sphinx_view/base.html",
    #     ),
    #     name="documentation",
    # ),
]

# Translatable URLs
# These will be available under a language code prefix. For example /en/search/
urlpatterns += i18n_patterns(
    path("", include(wagtail_urls)),
)


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
