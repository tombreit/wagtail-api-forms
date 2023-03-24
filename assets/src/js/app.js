// require ../../../node_modules/jquery/dist/jquery.min.js
// require ../../../node_modules/popper.js/dist/umd/popper.min.js
// require ../../../node_modules/bootstrap/dist/js/bootstrap.min.js
// require ../../../node_modules/select2/dist/js/select2.min.js
// require ../../../node_modules/flatpickr/dist/flatpickr.min.js
// require ../../../staticfiles/django_select2/django_select2.js

document.addEventListener("DOMContentLoaded", function(event) {

  const isFirefox = typeof InstallTrigger !== 'undefined';

  if (isFirefox) {
    // console.log("isFirefox:", isFirefox)

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
});
