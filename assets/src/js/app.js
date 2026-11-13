import * as bootstrap from 'bootstrap';
import flatpickr from "flatpickr";
import TomSelect from 'tom-select';

import { initFormSteps } from './form-steps';


// A listener of its own, so nothing else can keep multi-step forms from working
document.addEventListener('DOMContentLoaded', () => initFormSteps());

// "Reset" clears all answers (and uploads): ask first. In the capture phase, so
// a cancelled reset reaches no other listener (e.g. of multi-step forms) as such
document.addEventListener(
  'reset',
  (event) => {
    const message = event.target.dataset?.resetConfirm;
    if (message && !window.confirm(message)) {
      event.preventDefault();
    }
  },
  { capture: true },
);

// Tom Select doesn't notice a form reset: once the browser has reset the
// fields (after this event), update each one from its select
document.addEventListener('reset', ({ target: form, defaultPrevented }) => {
  if (defaultPrevented) {
    return;
  }
  setTimeout(() => {
    for (const select of form.querySelectorAll('select')) {
      select.tomselect?.sync();
    }
  });
});


document.addEventListener("DOMContentLoaded", function(event) {
  const isFirefox = typeof InstallTrigger !== 'undefined';

  if (isFirefox) {
    const flatpickrConfig = {
      allowInput: false,
      enableTime: true,
      altInput: true,
      dateFormat: "Y-m-dTH:i", // YYYY-MM-DD hh:mm
      time_24hr: true,
      weekNumbers: true,
      defaultHour: 9,
    }
    // const dateInputs = document.querySelectorAll(`input[type="datetime-local"]:not([readonly])`);
    // flatpickr(dateInputs, flatpickrConfig);
    flatpickr("input[type=datetime-local]", flatpickrConfig);
  }

  document.querySelectorAll('.is-tom-select').forEach((el)=>{
    let tomSelectconfig = {
        plugins: ['remove_button'],
        create: false,
        maxOptions: null,
        closeAfterSelect: true,
    };
    new TomSelect(el, tomSelectconfig);
  });

  document.querySelectorAll('a[href^="http"], a[href^="/documents/"]').forEach(link => {
    link.setAttribute('target', '_blank');
    link.setAttribute('rel', 'nofollow noopener');
  });

});
