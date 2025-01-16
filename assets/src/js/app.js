import * as bootstrap from 'bootstrap';
import flatpickr from "flatpickr";
import TomSelect from 'tom-select';


document.addEventListener("DOMContentLoaded", function(event) {
  const isFirefox = typeof InstallTrigger !== 'undefined';

  if (isFirefox) {
    flatpickrConfig = {
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
    };
    new TomSelect(el, tomSelectconfig);
  });

  document.querySelectorAll('a[href^="http"], a[href^="/documents/"]').forEach(link => {
    link.setAttribute('target', '_blank');
    link.setAttribute('rel', 'nofollow noopener');
  });

});
