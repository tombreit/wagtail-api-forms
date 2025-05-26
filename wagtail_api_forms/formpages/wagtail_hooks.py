from django.utils.safestring import mark_safe
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
    return mark_safe("""
    <script>
    window.addEventListener('DOMContentLoaded', (event) => {
        // Wrap in try-catch to prevent script failures
        try {
            const sequenceContainer = document.getElementById('id_form_fields-FORMS');
            if (!sequenceContainer) {
                console.warn('Form fields container not found');
                return;
            }

            const child_nodes = sequenceContainer.childNodes;

            for (const node of child_nodes) {
                if (node.nodeType === Node.ELEMENT_NODE && node.hasAttribute("data-inline-panel-child")) {
                    const idNr = node.id.replace("inline_child_form_fields-", "");
                    const inputId = "id_form_fields-" + idNr + "-label";
                    const labelElement = document.getElementById(inputId);

                    if (!labelElement) {
                        console.warn(`Label element not found for id: ${inputId}`);
                        continue;
                    }

                    const fieldName = labelElement.value;
                    const heading_elem = node.querySelector('[data-panel-heading-text]');

                    if (heading_elem) {
                        heading_elem.insertAdjacentText('beforeend', ": " + fieldName);
                    }
                }
            }

            // Collapse all form fields
            const formFieldTogglers = document.querySelectorAll("#id_form_fields-FORMS .w-panel__toggle");
            for (const formFieldToggle of formFieldTogglers) {
                formFieldToggle.click();
            }
        } catch (error) {
            console.error('Error in form fields initialization:', error);
        }
    });
    </script>
    """)


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
