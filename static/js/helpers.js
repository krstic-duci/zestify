/**
 * Shows a global notification banner with the given message and type.
 * Used for error and success messages throughout the app.
 */
function showGlobalNotification(message, type = 'error') {
    const container = document.getElementById('global-notification-container');
    if (!container) {
        console.error('Global notification container not found!');
        return;
    }

    const existingBanner = container.querySelector('.notification-banner');
    if (existingBanner) {
        existingBanner.remove();
    }

    const banner = document.createElement('div');
    banner.className = `notification-banner notification-${type}`;
    banner.textContent = message;

    container.appendChild(banner);

    setTimeout(() => {
        banner.style.opacity = '0';
        setTimeout(() => banner.remove(), 300);
    }, 5000);
}

/**
 * Makes an API request to the given endpoint with the specified method and body.
 * Handles JSON-only responses, 401 redirects, and user-friendly error notifications.
 * For POST endpoints, always expects JSON. For non-JSON, shows a friendly message.
 */
async function apiClient(endpoint, { method = 'POST', body = null } = {}) {
    const loader = document.getElementById('global-loader');
    if (loader) loader.classList.remove('hidden');

    try {
        const response = await fetch(endpoint, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: body ? JSON.stringify(body) : null
        });

        const contentType = response.headers.get("content-type");
        let result = null;
        if (contentType && contentType.includes("application/json")) {
            result = await response.json();
        }

        // Handle 401: redirect to login
        if (response.status === 401) {
            window.location.href = '/login';
            return { status: 'error', error: { code: ErrorCode.Api.UNAUTHORIZED, message: 'Not authenticated.' } };
        }

        // Handle other errors
        if (!response.ok) {
            const errorMsg = result?.error?.message || result?.message || 'An unknown server error occurred.';
            showGlobalNotification(errorMsg);
            return { status: 'error', error: { code: ErrorCode.Client.SERVER_ERROR, message: errorMsg } };
        }

        // If not JSON, treat as server bug for POST endpoints
        if (!result && method !== 'GET') {
            showGlobalNotification('Something went wrong. Please try again later.');
            return { status: 'error', error: { code: ErrorCode.Client.NON_JSON, message: 'Something went wrong. Please try again later.' } };
        }

        return result;

    } catch (error) {
        showGlobalNotification(error.message || 'Network error');
        return { status: 'error', error: { code: ErrorCode.Client.NETWORK_ERROR, message: error.message } };
    } finally {
        if (loader) loader.classList.add('hidden');
    }
}
