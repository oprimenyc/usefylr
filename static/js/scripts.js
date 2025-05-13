/**
 * Federal Funding Club - DIY Business Tax Tool
 * Main JavaScript file for global functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();
    
    // Initialize popovers
    initPopovers();
    
    // Handle flash message dismissal
    setupFlashMessages();
    
    // Enable responsive table handling
    setupResponsiveTables();
    
    // Initialize any date pickers
    initDatePickers();
    
    // Setup form validation
    setupFormValidation();
});

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover'
        });
    });
}

/**
 * Initialize Bootstrap popovers
 */
function initPopovers() {
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Setup flash message auto-dismissal
 */
function setupFlashMessages() {
    // Auto-dismiss flash messages after 5 seconds
    setTimeout(function() {
        var flashMessages = document.querySelectorAll('.alert-dismissible');
        flashMessages.forEach(function(message) {
            var closeButton = message.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        });
    }, 5000);
}

/**
 * Make tables responsive on small screens
 */
function setupResponsiveTables() {
    var tables = document.querySelectorAll('table');
    tables.forEach(function(table) {
        if (!table.parentElement.classList.contains('table-responsive')) {
            var wrapper = document.createElement('div');
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
    // This is a placeholder for potential datepicker initialization
    // In a real implementation, you might use a library like Flatpickr
    var dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function(input) {
        // Add any special handling for date inputs here
    });
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    // Add client-side validation to forms with validation-required class
    var forms = document.querySelectorAll('.validation-required');
    
    forms.forEach(function(form) {
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
    const options = format === 'short' 
        ? { year: 'numeric', month: 'numeric', day: 'numeric' }
        : { year: 'numeric', month: 'long', day: 'numeric' };
    
    return new Intl.DateTimeFormat('en-US', options).format(date);
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
    
    if (show) {
        const spinnerHtml = `
            <div class="text-center" id="loading-spinner-${containerId}">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">${message}</p>
            </div>
        `;
        container.innerHTML = spinnerHtml;
    } else {
        const spinner = document.getElementById(`loading-spinner-${containerId}`);
        if (spinner) {
            spinner.remove();
        }
    }
}

/**
 * Validate tax identification numbers
 * @param {string} type - The type of tax ID ('ein' or 'ssn')
 * @param {string} value - The value to validate
 * @returns {boolean} Whether the value is valid
 */
function validateTaxId(type, value) {
    if (!value) return false;
    
    const einRegex = /^\d{2}-\d{7}$/;
    const ssnRegex = /^\d{3}-\d{2}-\d{4}$/;
    
    if (type === 'ein') {
        return einRegex.test(value);
    } else if (type === 'ssn') {
        return ssnRegex.test(value);
    }
    
    return false;
}

/**
 * Send analytics event
 * @param {string} category - Event category
 * @param {string} action - Event action
 * @param {string} label - Event label
 */
function trackEvent(category, action, label) {
    // This is a placeholder for real analytics tracking
    console.log('TRACKING:', category, action, label);
    
    // In a real implementation, this would integrate with an analytics service
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
