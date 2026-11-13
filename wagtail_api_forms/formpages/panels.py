import json

from wagtail.admin.panels import FieldPanel


class FieldTypePanel(FieldPanel):
    """
    A FieldPanel of a form field that is only shown for some field types.

    Uses Wagtail's `w-rules` admin controller, which is set on the InlinePanel
    of the form fields (see FormPage.content_panels): it hides this panel while
    the field type of the same form field has another value. A hidden panel is
    still submitted, so its value is kept.
    """

    def __init__(self, field_name, field_types, **kwargs):
        super().__init__(field_name, **kwargs)
        self.field_types = field_types

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs["field_types"] = self.field_types
        return kwargs

    class BoundPanel(FieldPanel.BoundPanel):
        @property
        def attrs(self):
            # e.g. {"form_fields-3-field_type": ["dropdown", "radio", ...]}
            rules = {self.form.add_prefix("field_type"): list(self.panel.field_types)}
            return {
                **self.panel.attrs,
                "data-w-rules-target": "show",
                "data-w-rules": json.dumps(rules),
            }
