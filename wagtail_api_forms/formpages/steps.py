"""
Multi-step forms.

Page breaks among the form fields split a form into steps. All steps are part
of one HTML form: the browser shows one step at a time, and validates each step
on the server before moving on (see FormPage.serve_step_validation and
assets/src/js/form-steps.js). The form is submitted once, with the answers of
all steps, just like a form without page breaks.
"""

from dataclasses import dataclass, field

from .constants import PAGE_BREAK


def get_field_name(form_field):
    """The name of a form field's answer, also for unsaved fields (previews)."""
    return form_field.clean_name or form_field.get_field_clean_name()


@dataclass
class FormStep:
    """One step of a multi-step form: the form fields between two page breaks."""

    number: int
    heading: str = ""
    fields: list = field(default_factory=list)

    @property
    def field_names(self):
        return [get_field_name(form_field) for form_field in self.fields]


def split_into_steps(form_fields):
    """Split the form fields (incl. page breaks) into steps at each page break."""
    steps = [FormStep(number=1)]

    for form_field in form_fields:
        current_step = steps[-1]
        if form_field.field_type != PAGE_BREAK:
            current_step.fields.append(form_field)
        elif not current_step.fields:
            # A page break at the start of a step only sets its heading
            current_step.heading = form_field.heading
        else:
            steps.append(FormStep(number=len(steps) + 1, heading=form_field.heading))

    # Ignore a page break after the last field
    if len(steps) > 1 and not steps[-1].fields:
        steps.pop()

    return steps


@dataclass
class BoundStep:
    """A step with the bound fields of a form, for rendering."""

    number: int
    heading: str
    fields: list

    @property
    def has_errors(self):
        return any(bound_field.errors for bound_field in self.fields)


def bind_steps(steps, form):
    """
    The steps with the bound fields of `form`. Fields of the form which belong
    to no step, i.e. the captcha, go into the last step.
    """
    bound_steps = []
    step_field_names = set()
    for step in steps:
        names = [name for name in step.field_names if name in form.fields]
        step_field_names.update(names)
        bound_steps.append(
            BoundStep(
                number=step.number,
                heading=step.heading,
                fields=[form[name] for name in names],
            )
        )
    bound_steps[-1].fields += [
        form[name] for name in form.fields if name not in step_field_names
    ]
    return bound_steps
