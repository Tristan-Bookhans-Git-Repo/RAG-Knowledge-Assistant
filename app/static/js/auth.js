function attachAuthForm(formId, errorId, url, onSuccessRedirect) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const errorEl = document.getElementById(errorId);
        errorEl.hidden = true;

        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: form.elements.email.value,
                password: form.elements.password.value,
            }),
        });

        if (!response.ok) {
            const body = await response.json().catch(() => ({}));
            errorEl.textContent = body.detail || "Something went wrong. Please try again.";
            errorEl.hidden = false;
            return;
        }

        window.location.href = onSuccessRedirect;
    });
}

attachAuthForm("login-form", "login-error", "/auth/login", "/dashboard");
attachAuthForm("register-form", "register-error", "/auth/register", "/login");
