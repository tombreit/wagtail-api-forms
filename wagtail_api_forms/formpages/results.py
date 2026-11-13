"""
Poll results: how often each choice of the choice questions of a form was
chosen, shown after submitting a form with `FormPage.show_results` enabled.

Only choice questions are counted. Answers to other questions are never
shown: they may contain personal data.
"""

from collections import Counter
from dataclasses import dataclass, field

from .constants import CHOICE_FIELD_TYPES, MULTIPLE_CHOICE_FIELD_TYPES
from .steps import get_field_name


@dataclass
class ChoiceResult:
    label: str
    count: int
    percent: int
    # Chosen by the visitor, who has just submitted the form
    chosen: bool = False


@dataclass
class QuestionResult:
    question: str
    # Submissions with at least one choice of this question
    answer_count: int
    choices: list = field(default_factory=list)
    # The percentages of a question with several choices may add up to more than 100
    multiple: bool = False


def get_results(page, form_submission=None):
    """
    Count the choices of the choice questions of `page` in all its
    submissions, and mark the choices of `form_submission`.

    Answers which are no choice (anymore), e.g. after a choice has been
    renamed, are not counted.
    """
    questions = [
        form_field
        for form_field in page.get_form_fields()
        if form_field.field_type in CHOICE_FIELD_TYPES
    ]
    if not questions or not page.pk:
        # An unsaved page (admin preview) has no submissions
        return []

    # The choices of each question, in the editor's order
    form_builder = page.form_builder([])
    choices = {
        get_field_name(question): [
            value for value, label in form_builder.get_formatted_field_choices(question)
        ]
        for question in questions
    }

    def get_chosen(form_data, name):
        answer = form_data.get(name) or []
        answer = answer if isinstance(answer, list) else [answer]
        return [choice for choice in answer if choice in choices[name]]

    answer_counts = Counter()
    choice_counts = {name: Counter() for name in choices}
    submissions = page.get_submissions().values_list("form_data", flat=True)
    for form_data in submissions.iterator():
        for name in choices:
            if chosen := get_chosen(form_data, name):
                answer_counts[name] += 1
                choice_counts[name].update(chosen)

    own_answers = form_submission.form_data if form_submission else {}
    results = []
    for question in questions:
        name = get_field_name(question)
        answer_count = answer_counts[name]
        own_choices = get_chosen(own_answers, name)
        results.append(
            QuestionResult(
                question=question.label,
                answer_count=answer_count,
                # All choices, also those nobody has chosen
                choices=[
                    ChoiceResult(
                        label=choice,
                        count=choice_counts[name][choice],
                        percent=(
                            round(100 * choice_counts[name][choice] / answer_count)
                            if answer_count
                            else 0
                        ),
                        chosen=choice in own_choices,
                    )
                    for choice in choices[name]
                ],
                multiple=question.field_type in MULTIPLE_CHOICE_FIELD_TYPES,
            )
        )
    return results
