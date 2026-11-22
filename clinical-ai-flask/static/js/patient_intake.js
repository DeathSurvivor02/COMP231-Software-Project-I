/* ============================================================
   CLINICAL AI SUITE - PATIENT INTAKE CLIENT SCRIPT
   COMP231 - Software Development Project I (Group 1)
   Module Owner: Joel (Patient Experience Developer)
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
    const intakeForm = document.getElementById("intakeForm");
    const submitBtn = document.getElementById("submitBtn");
    const dobInput = document.getElementById("dob");

    if (dobInput) {
        // Set max date for Date of Birth to today
        const today = new Date().toISOString().split("T")[0];
        dobInput.setAttribute("max", today);
    }

    if (intakeForm && submitBtn) {
        intakeForm.addEventListener("submit", (e) => {
            if (dobInput && dobInput.value) {
                const selectedDob = new Date(dobInput.value);
                const now = new Date();
                if (selectedDob > now) {
                    e.preventDefault();
                    alert("Date of birth cannot be in the future.");
                    dobInput.focus();
                    return;
                }
            }

            submitBtn.disabled = true;
            submitBtn.textContent = "Submitting Intake...";
        });
    }
});
