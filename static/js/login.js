document.addEventListener('DOMContentLoaded', function () {
    const url = new URL(window.location.href);
    url.searchParams.delete('error');
    window.history.replaceState({}, document.title, url.pathname);

    const errorMessageDiv = document.querySelector('.error-message');
    if (errorMessageDiv) {
        setTimeout(() => {
            errorMessageDiv.remove();
        }, 5000);
    }
});
