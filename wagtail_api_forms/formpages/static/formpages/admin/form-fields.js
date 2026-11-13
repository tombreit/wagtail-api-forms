/**
 * The form fields of a form page in the page editor, see FormPage.content_panels.
 *
 * - Titles the panel of each form field with its label and its field type,
 *   kept up to date while editing. Page breaks are titled with their heading
 *   and the step they start ("Step 2"), so the steps of a multi-step form can
 *   be seen in the list of collapsed form fields.
 * - Collapses the panels of saved form fields, for an overview of the form.
 *   Wagtail keeps panels with errors expanded.
 *
 * Which attributes of a form field are shown for its field type is decided by
 * Wagtail's own w-rules controller, see panels.FieldTypePanel.
 *
 * A Stimulus controller, registered with Wagtail's Stimulus application:
 * https://docs.wagtail.org/en/stable/extending/client_side.html
 */

const { Controller } = window.StimulusModule;

class FormFieldsController extends Controller {
  static values = {
    // The field type of page breaks, constants.PAGE_BREAK
    pageBreak: String,
    // Translated, e.g. "Step %(number)s"
    stepLabel: String,
  };

  #observer;
  #frame = null;

  connect() {
    for (const child of this.#children()) {
      if (child.querySelector('input[name$="-id"]')?.value) {
        // Wagtail collapses panels with this class once the page has loaded
        child.querySelector('[data-panel]')?.classList.add('collapsed');
      }
    }
    this.updateTitles();

    // Moving a form field up or down (or dragging it) reorders the panels
    // without an event; the steps after it change
    const container = this.element.querySelector('[id$="-FORMS"]');
    if (container) {
      this.#observer = new MutationObserver(() => this.update());
      this.#observer.observe(container, { childList: true });
    }
    this.element.addEventListener('w-formset:added', this);
    this.element.addEventListener('w-formset:removed', this);
  }

  disconnect() {
    this.#observer?.disconnect();
    this.element.removeEventListener('w-formset:added', this);
    this.element.removeEventListener('w-formset:removed', this);
  }

  handleEvent() {
    this.update();
  }

  /**
   * Update the titles of all form fields, at most once per frame: a label or
   * field type changes, or form fields are added, deleted or moved.
   */
  update() {
    if (this.#frame === null) {
      this.#frame = requestAnimationFrame(() => {
        this.#frame = null;
        this.updateTitles();
      });
    }
  }

  updateTitles() {
    // The same rules as steps.split_into_steps(): a page break only starts a
    // new step after form fields, one at the start sets the first step's heading
    let step = 1;
    let stepHasFields = false;
    for (const child of this.#children()) {
      if (child.classList.contains('deleted')) {
        continue;
      }
      const isPageBreak = this.#input(child, 'field_type')?.value === this.pageBreakValue;
      if (isPageBreak && stepHasFields) {
        step += 1;
        stepHasFields = false;
      } else if (!isPageBreak) {
        stepHasFields = true;
      }
      this.#updateTitle(child, isPageBreak ? step : null);
    }
  }

  #children() {
    return this.element.querySelectorAll('[data-inline-panel-child]');
  }

  #input(child, name) {
    return child.querySelector(`[name$="-${name}"]`);
  }

  #updateTitle(child, stepNumber) {
    const headingText = child.querySelector('[data-panel-heading-text]');
    if (!headingText) {
      return;
    }
    const fieldType = this.#input(child, 'field_type');
    const title =
      this.#input(child, 'label')?.value.trim() || this.#input(child, 'heading')?.value.trim();
    const tagText =
      stepNumber !== null
        ? this.stepLabelValue.replace('%(number)s', stepNumber)
        : fieldType?.value && fieldType.selectedOptions[0]?.text.trim();

    let summary = headingText.querySelector(':scope > [data-form-field-summary]');
    if (!summary) {
      // Wagtail's heading ends with whitespace, which would precede the colon
      while (
        headingText.lastChild?.nodeType === Node.TEXT_NODE &&
        !headingText.lastChild.data.trim()
      ) {
        headingText.lastChild.remove();
      }
      summary = document.createElement('span');
      summary.dataset.formFieldSummary = '';
      headingText.append(summary);
    }
    summary.replaceChildren();
    if (title) {
      summary.append(`: ${title} `);
    }
    if (tagText) {
      const tag = document.createElement('span');
      // Wagtail's status tag; page breaks stand out as the start of a step
      tag.className = stepNumber !== null ? 'w-status w-status--primary' : 'w-status';
      tag.textContent = tagText;
      summary.append(' ', tag);
    }
  }
}

window.wagtail.app.register('waf-form-fields', FormFieldsController);
