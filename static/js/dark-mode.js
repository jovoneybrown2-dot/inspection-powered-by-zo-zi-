/**
 * Universal Dark Mode Toggle
 * Manages theme switching across all pages with localStorage persistence
 */

// Toggle between light and dark themes
function toggleTheme() {
    const body = document.body;
    const themeBtn = document.querySelector('.theme-toggle-btn');
    const currentTheme = body.getAttribute('data-theme');

    if (currentTheme === 'dark') {
        // Switch to light mode
        body.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
        if (themeBtn) {
            themeBtn.textContent = 'Dark';
        }
    } else {
        // Switch to dark mode
        body.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        if (themeBtn) {
            themeBtn.textContent = 'Light';
        }
    }
}

// Load saved theme preference on page load
function loadSavedTheme() {
    const savedTheme = localStorage.getItem('theme');
    const themeBtn = document.querySelector('.theme-toggle-btn');

    if (savedTheme === 'dark') {
        document.body.setAttribute('data-theme', 'dark');
        if (themeBtn) {
            themeBtn.textContent = 'Light';
        }
    } else {
        // Ensure light mode is set
        document.body.removeAttribute('data-theme');
        if (themeBtn) {
            themeBtn.textContent = 'Dark';
        }
    }
}

// Initialize theme when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadSavedTheme);
} else {
    // DOM already loaded
    loadSavedTheme();
}