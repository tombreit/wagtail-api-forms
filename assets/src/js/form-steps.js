// Multi-step forms, see wagtail_api_forms/formpages/steps.py
//
// All steps are rendered into one form (formpages/includes/form_steps.html).
// FormSteps shows one step at a time and validates each step on the server
// before moving on. The form is submitted once, with the answers of all
// steps, and validated again as a whole.

const INVALID_CLASS = 'is-invalid';
// Show that a step is being checked only if it takes a moment, without flicker
const BUSY_DELAY = 250;

export class FormSteps {
  #form;
  #steps;
  #buttons;
  #stepErrors;
  #spinner;
  #status;
  // Empty in the admin preview: steps are not validated there
  #validationUrl;
  #current = 0;
  #busy = false;

  constructor(form) {
    this.#form = form;
    this.#steps = [...form.querySelectorAll('[data-form-step]')];
    this.#buttons = {
      back: form.querySelector('[data-step-back]'),
      next: form.querySelector('[data-step-next]'),
      reset: form.querySelector('[data-step-reset]'),
      submit: form.querySelector('[data-step-submit]'),
    };
    this.#stepErrors = form.querySelector('[data-step-errors]');
    this.#spinner = form.querySelector('[data-step-spinner]');
    this.#status = form.querySelector('[data-step-status]');
    this.#validationUrl = form.dataset.stepValidationUrl;

    this.#buttons.back.addEventListener('click', () => this.show(this.#current - 1));
    this.#buttons.next.addEventListener('click', () => this.next());
    form.addEventListener('submit', (event) => this.#onSubmit(event));
    form.addEventListener('reset', (event) => this.#onReset(event));
    // The error summary after an invalid submission links to fields of all steps
    form
      .querySelector('[data-error-summary]')
      ?.addEventListener('click', (event) => this.#onErrorLink(event));

    // After an invalid submission: the first step with errors
    const initialStep = parseInt(form.dataset.initialStep, 10) || 1;
    this.show(Math.min(Math.max(initialStep, 1), this.#steps.length) - 1, {
      focus: false,
    });
  }

  get #isLast() {
    return this.#current === this.#steps.length - 1;
  }

  show(index, { focus = true } = {}) {
    this.#current = index;
    this.#steps.forEach((step, i) => {
      step.hidden = i !== index;
    });
    const { back, next, reset, submit } = this.#buttons;
    back.hidden = index === 0;
    next.hidden = this.#isLast;
    reset.hidden = !this.#isLast;
    submit.hidden = !this.#isLast;
    this.#stepErrors.hidden = true;

    if (focus) {
      this.#scrollToStep();
      // Screen readers continue with the new step, named by its position and heading
      const step = this.#steps[index];
      step.tabIndex = -1;
      step.focus({ preventScroll: true });
    }
  }

  /** Validate the current step, then move on to the next one. */
  async next() {
    if (this.#busy || this.#isLast) {
      return;
    }
    this.#busy = true;
    this.#buttons.next.disabled = true;
    const step = this.#steps[this.#current];
    const busyTimer = setTimeout(() => this.#setBusy(step, true), BUSY_DELAY);
    try {
      const errors = await this.#validate(step);
      this.#clearErrors(step);
      if (Object.keys(errors).length) {
        this.#showErrors(step, errors);
      } else {
        this.show(this.#current + 1);
      }
    } finally {
      clearTimeout(busyTimer);
      this.#setBusy(step, false);
      this.#busy = false;
      this.#buttons.next.disabled = false;
    }
  }

  // E.g. while the uploads of a step are being checked
  #setBusy(step, busy) {
    this.#spinner.hidden = !busy;
    step.toggleAttribute('aria-busy', busy);
    this.#status.textContent = busy ? this.#status.dataset.busyText : '';
  }

  #onSubmit(event) {
    // Enter in a field submits the form: move to the next step instead
    if (!this.#isLast) {
      event.preventDefault();
      this.next();
    }
  }

  // Tom Select is updated on reset for all forms, see app.js
  #onReset(event) {
    // Cancelled by the visitor (confirmation in app.js)
    if (event.defaultPrevented) {
      return;
    }
    this.#steps.forEach((step) => this.#clearErrors(step));
    this.show(0);
  }

  // Open the step of the field an error summary link points to
  #onErrorLink(event) {
    const link = event.target.closest('a[href^="#"]');
    const target = link && document.getElementById(link.hash.slice(1));
    const index = this.#steps.findIndex((step) => step.contains(target));
    if (index === -1) {
      return;
    }
    event.preventDefault();
    this.show(index, { focus: false });
    target.scrollIntoView({ block: 'center' });
    this.#focusFirstControl(target);
  }

  #focusFirstControl(wrapper) {
    // Hidden controls (e.g. replaced by Tom Select) can't take the focus
    const focusable = [...wrapper.querySelectorAll('input, select, textarea')].find(
      (el) => el.type !== 'hidden' && el.offsetParent !== null,
    );
    focusable?.focus({ preventScroll: true });
  }

  #scrollToStep() {
    if (window.parentIframe) {
      // Embedded (?embed=true): scroll the embedding page to the iframe's top
      window.parentIframe.scrollToOffset(0, 0);
    } else {
      this.#steps[this.#current].scrollIntoView({ block: 'start' });
    }
  }

  // The answers of one step: uploads of the other steps are not sent along
  #getStepData(step) {
    const names = new Set([...step.elements].map((el) => el.name).filter(Boolean));
    const data = new FormData();
    for (const [name, value] of new FormData(this.#form)) {
      if (names.has(name)) {
        data.append(name, value);
      }
    }
    data.append('csrfmiddlewaretoken', this.#form.elements.csrfmiddlewaretoken.value);
    data.append('form_step', step.dataset.formStep);
    return data;
  }

  // The errors of the step, e.g. {email: [{message: "…", code: "…"}]}
  async #validate(step) {
    if (!this.#validationUrl) {
      return {};
    }
    try {
      const response = await fetch(this.#validationUrl, {
        method: 'POST',
        body: this.#getStepData(step),
        credentials: 'same-origin',
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const { errors } = await response.json();
      return errors ?? {};
    } catch (error) {
      // The submitted form is validated again: don't keep visitors from
      // moving on because a step could not be checked
      console.warn('This step could not be validated:', error);
      return {};
    }
  }

  #clearErrors(step) {
    // Ours and the ones rendered by the server after an invalid submission
    step.querySelectorAll('.invalid-feedback').forEach((el) => el.remove());
    step.querySelectorAll(`.${INVALID_CLASS}`).forEach((el) => {
      el.classList.remove(INVALID_CLASS);
    });
    this.#stepErrors.hidden = true;
  }

  #showErrors(step, errors) {
    let firstWrapper = null;
    for (const [name, messages] of Object.entries(errors)) {
      const controls = [...step.elements].filter((el) => el.name === name);
      controls.forEach((el) => el.classList.add(INVALID_CLASS));

      // The field's wrapper rendered by crispy-forms
      const wrapper =
        step.querySelector(`#div_id_${CSS.escape(name)}`) ?? controls[0]?.parentElement;
      if (!wrapper) {
        continue;
      }
      const feedback = document.createElement('div');
      feedback.className = 'invalid-feedback d-block';
      feedback.textContent = messages.map(({ message }) => message).join(' ');
      wrapper.append(feedback);
      firstWrapper ??= wrapper;
    }

    this.#stepErrors.hidden = false;
    if (firstWrapper) {
      firstWrapper.scrollIntoView({ block: 'center' });
      this.#focusFirstControl(firstWrapper);
    }
  }
}

export function initFormSteps(root = document) {
  for (const form of root.querySelectorAll('form[data-form-steps]')) {
    if (form.querySelectorAll('[data-form-step]').length > 1) {
      new FormSteps(form);
    }
  }
}
