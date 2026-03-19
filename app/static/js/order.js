document.addEventListener("DOMContentLoaded", function() {
    const cancelForms = document.querySelectorAll("form");

    cancelForms.forEach(form => {
        form.addEventListener("submit", function(e) {
            if (!confirm("Are you sure you want to cancel this order?")) {
                e.preventDefault();
                return;
            }
            const submitter = e.submitter;
            if (submitter) {
                submitter.disabled = true;
            }
        });
    });
});