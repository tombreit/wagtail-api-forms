from django.utils.safestring import mark_safe
from wagtail import hooks
# from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register  # ModelAdminGroup
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

from .models import Attachment, TokenForm


@hooks.register('construct_page_action_menu')
def make_publish_default_action(menu_items, request, context):
    for (index, item) in enumerate(menu_items):
        if item.name == 'action-publish':
            # move to top of list
            menu_items.pop(index)
            menu_items.insert(0, item)
            break


@hooks.register('construct_main_menu')
def hide_explorer_menu_items_images_and_docs(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name not in ['images', 'documents']]


@hooks.register('insert_editor_js')
def editor_js():
    return mark_safe("""
    <script>
    window.addEventListener('DOMContentLoaded', (event) => {
        // console.log("Accordionize fields list...")

        /* Display field name/label in wagtail admin interface as field heading */
        const sequenceContainer = document.getElementById('id_form_fields-FORMS');
        const child_nodes = sequenceContainer.childNodes;

        for (node of child_nodes){
            if (node.nodeType == Node.ELEMENT_NODE && node.hasAttribute("data-inline-panel-child")) {
                let idNr;
                idNr = node.id.replace("inline_child_form_fields-", "");
                const inputId = "id_form_fields-" + idNr + "-label";
                // Get input elem with "d_form_fields-0-label" value
                const fieldName = document.getElementById(inputId).value;
                // Get heading element: <span data-panel-heading-text>
                const heading_elem = node.querySelector('[data-panel-heading-text]');
                const appendFieldName = ": " + fieldName
                heading_elem.insertAdjacentText('beforeend', appendFieldName);
            }
        }

        /* Collapse all form fields on page load */
        const formFieldTogglers = document.querySelectorAll("#id_form_fields-FORMS .w-panel__toggle");

        for (formFieldToggle of formFieldTogglers){
            console.log(formFieldToggle);
            formFieldToggle.click();
        }
    });
    </script>
    """)


class AttachmentAdmin(ModelAdmin):
    model = Attachment
    menu_label = 'Attachments'  # ditch this to use verbose_name_plural from model
    menu_icon = 'pilcrow'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    # exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('created_at', 'modified_at', 'file', 'form_submission', 'av_scanned_at', 'av_reason', 'av_passed')
    list_filter = ('av_passed',)
    search_fields = ('file', 'av_reason')
    ordering = ('-created_at', '-modified_at')


class TokenFormAdmin(ModelAdmin):
    model = TokenForm
    menu_label = 'Token Forms'  # ditch this to use verbose_name_plural from model
    menu_icon = 'pilcrow'  # change as required
    menu_order = 300  # will put in 3rd place (000 being 1st, 100 2nd)
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    # exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('form', 'api_user')
    list_filter = ('form', 'api_user')
    search_fields = ('form', 'api_user')


modeladmin_register(TokenFormAdmin)
modeladmin_register(AttachmentAdmin)
