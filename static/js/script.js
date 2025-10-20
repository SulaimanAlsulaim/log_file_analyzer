document.addEventListener("DOMContentLoaded", function () {
  const forms = document.querySelectorAll("form");

  forms.forEach(form => {
    form.addEventListener("submit", function (e) {
      const inputs = form.querySelectorAll("input[required]");
      let valid = true;

      inputs.forEach(input => {
        if (!input.value.trim()) {
          valid = false;
        }
      });

      if (!valid) {
        alert("Please fill in all required fields.");
        e.preventDefault();
      }
    });
  });
});
