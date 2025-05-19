/**
 * Federal Funding Club - DIY Business Tax Tool
 * Main JavaScript file for global functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    initTooltips();
    
    // Initialize Bootstrap popovers
    initPopovers();
    
    // Setup flash message auto-dismissal
    setupFlashMessages();
    
    // Make tables responsive on small screens
    setupResponsiveTables();
    
    // Initialize date pickers
    initDatePickers();
    
    // Setup form validation
    setupFormValidation();
    
    // Setup theme switcher
    setupThemeSwitcher();
});

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize Bootstrap popovers
 */
function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Setup flash message auto-dismissal
 */
function setupFlashMessages() {
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    
    flashMessages.forEach(function(message) {
        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            const closeButton = message.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });
}

/**
 * Make tables responsive on small screens
 */
function setupResponsiveTables() {
    const tables = document.querySelectorAll('table');
    
    tables.forEach(function(table) {
        if (!table.parentElement.classList.contains('table-responsive')) {
            const wrapper = document.createElement('div');
            wrapper.classList.add('table-responsive');
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    });
}

/**
 * Initialize date pickers for date inputs
 */
function initDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    dateInputs.forEach(function(input) {
        // Add min and max attributes if not present
        if (!input.hasAttribute('min')) {
            const currentYear = new Date().getFullYear();
            input.setAttribute('min', `${currentYear - 10}-01-01`);
            input.setAttribute('max', `${currentYear + 1}-12-31`);
        }
    });
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Show guided tour of the application
 */
function showGuidedTour() {
    console.log("Guided tour button clicked");
    alert("The guided tour feature is being implemented. Thank you for your patience.");
}

/**
 * Format currency values
 * @param {number} value - The value to format
 * @param {string} currency - The currency code (default: USD)
 * @returns {string} Formatted currency string
 */
function formatCurrency(value, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(value);
}

/**
 * Format date values
 * @param {string} dateStr - The date string to format
 * @param {string} format - The format to use (default: 'medium')
 * @returns {string} Formatted date string
 */
function formatDate(dateStr, format = 'medium') {
    const date = new Date(dateStr);
    
    switch (format) {
        case 'short':
            return date.toLocaleDateString();
        case 'long':
            return date.toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        case 'medium':
        default:
            return date.toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
    }
}

/**
 * Show/hide loading spinner
 * @param {boolean} show - Whether to show or hide the spinner
 * @param {string} containerId - The ID of the container element
 * @param {string} message - Optional loading message
 */
function toggleLoadingSpinner(show, containerId, message = 'Loading...') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Remove existing spinner if any
    const existingSpinner = container.querySelector('.loading-spinner');
    if (existingSpinner) {
        existingSpinner.remove();
    }
    
    if (show) {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner text-center my-5';
        
        spinner.innerHTML = `
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p>${message}</p>
        `;
        
        container.prepend(spinner);
    }
}

/**
 * Validate tax identification numbers
 * @param {string} type - The type of tax ID ('ein' or 'ssn')
 * @param {string} value - The value to validate
 * @returns {boolean} Whether the value is valid
 */
function validateTaxId(type, value) {
    // Remove non-digit characters
    const digits = value.replace(/\D/g, '');
    
    switch (type) {
        case 'ein':
            // EIN: XX-XXXXXXX (9 digits)
            return digits.length === 9;
        case 'ssn':
            // SSN: XXX-XX-XXXX (9 digits)
            return digits.length === 9;
        default:
            return false;
    }
}

/**
 * Send analytics event
 * @param {string} category - Event category
 * @param {string} action - Event action
 * @param {string} label - Event label
 */
function trackEvent(category, action, label) {
    if (typeof gtag !== 'undefined') {
        gtag('event', action, {
            'event_category': category,
            'event_label': label
        });
    }
}

/**
 * Check if element is in viewport
 * @param {HTMLElement} el - The element to check
 * @returns {boolean} Whether the element is in viewport
 */
function isInViewport(el) {
    const rect = el.getBoundingClientRect();
    
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Setup theme switcher functionality
 */
function setupThemeSwitcher() {
    const toggleSwitch = document.getElementById('theme-toggle');
    if (!toggleSwitch) return;
    
    // Check for saved user preference
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Set initial theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    // Update toggle switch position
    if (currentTheme === 'dark') {
        toggleSwitch.checked = true;
    }
    
    // Add event listener for theme toggle
    toggleSwitch.addEventListener('change', function(e) {
        if (e.target.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    });
}