/**
 * Federal Funding Club - DIY Business Tax Tool
 * Form utilities for tax forms and IRS letters
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form navigation
    initFormNavigation();
    
    // Setup form section validation
    setupFormSectionValidation();
    
    // Setup currency formatting on input fields
    setupCurrencyFormatting();
    
    // Setup autosave functionality
    setupFormAutosave();
    
    // Format tax ID fields
    setupTaxIdFormatting();
});

/**
 * Initialize multi-step form navigation
 */
function initFormNavigation() {
    const formSections = document.querySelectorAll('.form-section');
    if (formSections.length <= 1) return;
    
    const nextButtons = document.querySelectorAll('.next-section');
    const prevButtons = document.querySelectorAll('.prev-section');
    const progressBar = document.getElementById('formProgress');
    
    // Set initial progress
    if (progressBar) {
        updateProgress(1, formSections.length);
    }
    
    // Add event listeners to next buttons
    nextButtons.forEach((button, index) => {
        button.addEventListener('click', function() {
            // Validate current section before proceeding
            if (!validateFormSection(formSections[index])) {
                return false;
            }
            
            // Hide current section, show next section
            formSections[index].style.display = 'none';
            formSections[index + 1].style.display = 'block';
            
            // Update progress
            if (progressBar) {
                updateProgress(index + 2, formSections.length);
            }
            
            // Scroll to top of the form
            scrollToElement(formSections[index + 1]);
        });
    });
    
    // Add event listeners to previous buttons
    prevButtons.forEach((button, index) => {
        button.addEventListener('click', function() {
            // Hide current section, show previous section
            formSections[index + 1].style.display = 'none';
            formSections[index].style.display = 'block';
            
            // Update progress
            if (progressBar) {
                updateProgress(index + 1, formSections.length);
            }
            
            // Scroll to top of the form
            scrollToElement(formSections[index]);
        });
    });
}

/**
 * Update progress bar
 * @param {number} current - Current step
 * @param {number} total - Total steps
 */
function updateProgress(current, total) {
    const progressBar = document.getElementById('formProgress');
    if (!progressBar) return;
    
    const percentage = Math.floor((current / total) * 100);
    progressBar.style.width = percentage + '%';
    progressBar.setAttribute('aria-valuenow', percentage);
}

/**
 * Validate a form section
 * @param {HTMLElement} section - The form section to validate
 * @returns {boolean} Whether the section is valid
 */
function validateFormSection(section) {
    const requiredFields = section.querySelectorAll('[required]');
    let valid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('invalid-feedback')) {
                const feedback = document.createElement('div');
                feedback.classList.add('invalid-feedback');
                feedback.textContent = 'This field is required.';
                field.parentNode.insertBefore(feedback, field.nextSibling);
            }
            valid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    if (!valid) {
        // Find first invalid input and focus it
        section.querySelector('.is-invalid').focus();
    }
    
    return valid;
}

/**
 * Setup validation for form sections
 */
function setupFormSectionValidation() {
    const inputFields = document.querySelectorAll('input, select, textarea');
    
    inputFields.forEach(field => {
        field.addEventListener('change', function() {
            if (this.hasAttribute('required')) {
                if (!this.value.trim()) {
                    this.classList.add('is-invalid');
                } else {
                    this.classList.remove('is-invalid');
                }
            }
            
            // Special validation for types
            if (this.dataset.type === 'currency') {
                validateCurrencyInput(this);
            } else if (this.dataset.type === 'tax_id') {
                validateTaxIdInput(this);
            }
        });
    });
}

/**
 * Validate currency input
 * @param {HTMLInputElement} input - The input element
 */
function validateCurrencyInput(input) {
    const value = input.value.replace(/[^0-9.]/g, '');
    const isValid = !isNaN(parseFloat(value)) && isFinite(value);
    
    if (!isValid && value !== '') {
        input.classList.add('is-invalid');
        if (!input.nextElementSibling || !input.nextElementSibling.classList.contains('invalid-feedback')) {
            const feedback = document.createElement('div');
            feedback.classList.add('invalid-feedback');
            feedback.textContent = 'Please enter a valid currency amount.';
            input.parentNode.insertBefore(feedback, input.nextSibling);
        }
    } else {
        input.classList.remove('is-invalid');
    }
}

/**
 * Validate tax ID input
 * @param {HTMLInputElement} input - The input element
 */
function validateTaxIdInput(input) {
    const value = input.value;
    let isValid = false;
    
    if (input.dataset.taxType === 'ein') {
        isValid = /^\d{2}-\d{7}$/.test(value);
    } else if (input.dataset.taxType === 'ssn') {
        isValid = /^\d{3}-\d{2}-\d{4}$/.test(value);
    }
    
    if (!isValid && value !== '') {
        input.classList.add('is-invalid');
        if (!input.nextElementSibling || !input.nextElementSibling.classList.contains('invalid-feedback')) {
            const feedback = document.createElement('div');
            feedback.classList.add('invalid-feedback');
            feedback.textContent = input.dataset.taxType === 'ein' 
                ? 'Please enter a valid EIN in the format XX-XXXXXXX.' 
                : 'Please enter a valid SSN in the format XXX-XX-XXXX.';
            input.parentNode.insertBefore(feedback, input.nextSibling);
        }
    } else {
        input.classList.remove('is-invalid');
    }
}

/**
 * Setup currency formatting for input fields
 */
function setupCurrencyFormatting() {
    const currencyInputs = document.querySelectorAll('input[data-type="currency"]');
    
    currencyInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            // Get input value and remove all non-digits
            let value = this.value.replace(/[^0-9.]/g, '');
            
            // Check if valid number
            if (value !== '' && !isNaN(parseFloat(value))) {
                // Format to 2 decimal places
                value = parseFloat(value).toFixed(2);
                
                // Add commas for thousands
                value = value.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
            }
            
            // Update input value
            this.value = value;
        });
    });
}

/**
 * Setup form autosave functionality
 */
function setupFormAutosave() {
    const form = document.querySelector('form[data-autosave="true"]');
    if (!form) return;
    
    const formInputs = form.querySelectorAll('input, select, textarea');
    const autosaveKey = form.dataset.autosaveKey || 'form_autosave';
    
    // Load autosaved data if exists
    const savedData = localStorage.getItem(autosaveKey);
    if (savedData) {
        try {
            const formData = JSON.parse(savedData);
            for (const key in formData) {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    input.value = formData[key];
                }
            }
            
            showAutosaveMessage('Form data has been restored from your last session.', 'info');
        } catch (e) {
            console.error('Error loading autosaved form data:', e);
        }
    }
    
    // Set up autosave on input change
    formInputs.forEach(input => {
        input.addEventListener('change', function() {
            autosaveForm(form, autosaveKey);
        });
    });
    
    // Autosave every 30 seconds
    setInterval(() => {
        autosaveForm(form, autosaveKey);
    }, 30000);
}

/**
 * Autosave form data
 * @param {HTMLFormElement} form - The form element
 * @param {string} key - The localStorage key
 */
function autosaveForm(form, key) {
    const formData = {};
    const formInputs = form.querySelectorAll('input, select, textarea');
    
    formInputs.forEach(input => {
        if (input.name && !input.name.includes('password')) {
            formData[input.name] = input.value;
        }
    });
    
    try {
        localStorage.setItem(key, JSON.stringify(formData));
        showAutosaveMessage('Form data autosaved', 'success');
    } catch (e) {
        console.error('Error autosaving form data:', e);
    }
}

/**
 * Show autosave message
 * @param {string} message - The message to show
 * @param {string} type - The message type
 */
function showAutosaveMessage(message, type) {
    const messageContainer = document.getElementById('autosave-message');
    if (!messageContainer) return;
    
    messageContainer.textContent = message;
    messageContainer.className = '';
    messageContainer.classList.add('text-' + type);
    
    // Clear message after 3 seconds
    setTimeout(() => {
        messageContainer.textContent = '';
    }, 3000);
}

/**
 * Setup formatting for tax ID fields
 */
function setupTaxIdFormatting() {
    const taxIdInputs = document.querySelectorAll('input[data-type="tax_id"]');
    
    taxIdInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            // Get input value and remove non-digits
            let value = this.value.replace(/\D/g, '');
            
            // Format based on tax ID type
            if (this.dataset.taxType === 'ein') {
                if (value.length > 2) {
                    value = value.substring(0, 2) + '-' + value.substring(2);
                }
                // Limit to XX-XXXXXXX format
                value = value.substring(0, 10);
            } else if (this.dataset.taxType === 'ssn') {
                if (value.length > 3) {
                    value = value.substring(0, 3) + '-' + value.substring(3);
                }
                if (value.length > 6) {
                    value = value.substring(0, 6) + '-' + value.substring(6);
                }
                // Limit to XXX-XX-XXXX format
                value = value.substring(0, 11);
            }
            
            // Update input value
            this.value = value;
        });
    });
}

/**
 * Calculate tax form totals
 * @param {string} formType - The type of tax form
 */
function calculateFormTotals(formType) {
    if (formType === '1120') {
        calculateForm1120Totals();
    } else if (formType === '1065') {
        calculateForm1065Totals();
    } else if (formType === 'Schedule C') {
        calculateScheduleCTotals();
    }
}

/**
 * Calculate Form 1120 totals
 */
function calculateForm1120Totals() {
    // Get income values
    const grossReceipts = parseFloat(document.getElementById('gross_receipts').value || 0);
    const returnsAllowances = parseFloat(document.getElementById('returns_allowances').value || 0);
    const otherIncome = parseFloat(document.getElementById('other_income').value || 0);
    
    // Calculate total income
    const totalIncome = grossReceipts - returnsAllowances + otherIncome;
    
    // Get deduction values
    const salariesWages = parseFloat(document.getElementById('salaries_wages').value || 0);
    const repairsMaintenance = parseFloat(document.getElementById('repairs_maintenance').value || 0);
    const rents = parseFloat(document.getElementById('rents').value || 0);
    const taxesLicenses = parseFloat(document.getElementById('taxes_licenses').value || 0);
    const interest = parseFloat(document.getElementById('interest').value || 0);
    const depreciation = parseFloat(document.getElementById('depreciation').value || 0);
    const otherDeductions = parseFloat(document.getElementById('other_deductions').value || 0);
    
    // Calculate total deductions
    const totalDeductions = salariesWages + repairsMaintenance + rents + taxesLicenses + interest + depreciation + otherDeductions;
    
    // Calculate taxable income
    const taxableIncome = totalIncome - totalDeductions;
    
    // Update total fields
    if (document.getElementById('total_income')) {
        document.getElementById('total_income').value = totalIncome.toFixed(2);
    }
    
    if (document.getElementById('total_deductions')) {
        document.getElementById('total_deductions').value = totalDeductions.toFixed(2);
    }
    
    if (document.getElementById('taxable_income')) {
        document.getElementById('taxable_income').value = taxableIncome.toFixed(2);
    }
}

/**
 * Scroll to element
 * @param {HTMLElement} element - The element to scroll to
 */
function scrollToElement(element) {
    window.scrollTo({
        top: element.offsetTop - 20,
        behavior: 'smooth'
    });
}
