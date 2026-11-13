from django.templatetags.static import static
from django.utils.html import format_html
from wagtail import hooks
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.ui.tables import BooleanColumn

from .models import Attachment, TokenForm


@hooks.register("construct_page_action_menu")
def make_publish_default_action(menu_items, request, context):
    for index, item in enumerate(menu_items):
        if item.name == "action-publish":
            # move to top of list
            menu_items.pop(index)
            menu_items.insert(0, item)
            break


@hooks.register("construct_main_menu")
def hide_explorer_menu_items_images_and_docs(request, menu_items):
    menu_items[:] = [
        item for item in menu_items if item.name not in ["images", "documents"]
    ]


@hooks.register("insert_editor_js")
def editor_js():
    # A Stimulus controller for the form fields of form pages, see the module
    return format_html(
        '<script type="module" src="{}"></script>',
        static("formpages/admin/form-fields.js"),
    )


class AttachmentAdminViewSet(ModelViewSet):
    model = Attachment
    form_fields = "__all__"
    menu_icon = "pilcrow"
    menu_label = "Attachments"
    menu_order = 300
    add_to_admin_menu = True
    add_to_settings_menu = True

    list_display = [
        "created_at",
        "modified_at",
        "file",
        "form_submission",
        "av_scanned_at",
        "av_reason",
        BooleanColumn("av_passed"),
    ]
    list_filter = ("av_passed",)
    search_fields = ["file", "av_reason"]
    ordering = ["-modified_at", "-created_at"]


class TokenFormAdminViewSet(ModelViewSet):
    model = TokenForm
    form_fields = "__all__"
    icon = "pilcrow"
    menu_label = "Token Forms"
    menu_order = 300
    add_to_admin_menu = True
    add_to_settings_menu = True

    list_display = ["form", "api_user"]
    list_filter = ["form", "api_user"]
    search_fields = ["form", "api_user"]


@hooks.register("register_admin_viewset")
def register_attachment_viewset():
    return AttachmentAdminViewSet()


@hooks.register("register_admin_viewset")
def register_tokenform_viewset():
    return TokenFormAdminViewSet()
