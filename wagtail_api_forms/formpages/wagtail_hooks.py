from django.utils.safestring import mark_safe
from wagtail import hooks
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register  # ModelAdminGroup

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
    return mark_safe(
        """
<script>
    // const styleElem = document.createElement("style");
    // styleElem.textContent = `
    //     #id_form_fields-FORMS summary {
    //         list-style: none;
    //         font-size: larger;
    //         padding-left: 1em;
    //     }
    //     #id_form_fields-FORMS summary::-webkit-details-marker {
    //         display: none;
    //     }
    //     #id_form_fields-FORMS summary::before {
    //         position: absolute;
    //         top: 0.75em;
    //         left: 3px;
    //         height: 1.75em;
    //         width: 1.75em;
    //         box-sizing: border-box;
    //         overflow: hidden;
    //         cursor: pointer;
    //         font-family: wagtail;
    //         content: "▾";
    //         text-align: center;
    //         background-color: var(--color-primary);
    //         border: 1px solid var(--color-primary);
    //         border-radius: 3px;
    //         color: #fff;
    //     }
    //     #id_form_fields-FORMS details[open] summary::before {
    //         content:"▴";
    //     }
    // `;
    // document.head.appendChild(styleElem);
    // function wrap(el, label) {
    //     let wrapper = document.createElement('details'),
    //         summaryElem = document.createElement('summary'),
    //         summaryCont = document.createTextNode(label);
    //     el.parentNode.insertBefore(wrapper, el);
    //     summaryElem.appendChild(summaryCont);
    //     // summaryElem.setAttribute("style", "font-size: larger");
    //     wrapper.appendChild(el);
    //     wrapper.insertAdjacentElement('afterbegin', summaryElem);
    // }
    // if (node.nodeName === "LI") {
    // for (fieldset of node.getElementsByTagName("fieldset")) {}
    // target_label_elem = fieldset.querySelector('[data-contentpath="label"] input');
    // target_label = target_label_elem.value;
    // wrap(fieldset, target_label);

    window.addEventListener('DOMContentLoaded', (event) => {
        // console.log("Accordionize fields list...")

        const sequenceContainer = document.getElementById('id_form_fields-FORMS');
        const child_nodes = sequenceContainer.childNodes;

        for (node of child_nodes){
            let idNr;
            if (node.nodeType == Node.ELEMENT_NODE && node.hasAttribute("data-inline-panel-child")) {
                idNr = node.id.replace("inline_child_form_fields-", "");
                const inputId = "id_form_fields-" + idNr + "-label";
                // Get input elem with "d_form_fields-0-label" value
                const fieldName = document.getElementById(inputId).value;
                // Get heading element: <span data-panel-heading-text>
                const heading_elem = node.querySelector('[data-panel-heading-text]');
                const appendFieldName = ": " + fieldName
                heading_elem.insertAdjacentText('beforeend', appendFieldName);

                // Initially collapse all fields
                // TODO: needs two clicks to uncollapse
                const toggleSectionId = "inline_child_form_fields-" + idNr + "-panel-content"
                const toggleSection = document.getElementById(toggleSectionId)
                toggleSection.setAttribute('hidden', '');
            }
        }
    });
</script>
"""
    )


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


# class FormGroup(ModelAdminGroup):
#     menu_label = 'Form Management'
#     menu_icon = 'folder-open-inverse'  # change as required
#     menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
#     items = (
#         AttachmentAdmin,
#         TokenFormAdmin,
#     )
# modeladmin_register(FormGroup)

modeladmin_register(TokenFormAdmin)
modeladmin_register(AttachmentAdmin)