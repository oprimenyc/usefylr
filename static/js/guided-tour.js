// Guided Tour Configuration
function showGuidedTour() {
    const intro = introJs();
    
    // Configure the steps of the tour based on current page
    const currentPath = window.location.pathname;
    
    if (currentPath === '/' || currentPath === '/index.html') {
        // Homepage tour
        intro.setOptions({
            steps: [
                {
                    title: 'Welcome to .fylr',
                    intro: 'Let\'s take a quick tour of our AI-powered tax platform. Click "Next" to continue.'
                },
                {
                    element: '.navbar-brand',
                    title: 'Navigation',
                    intro: 'Use the navigation menu to move around the platform. You can always return home by clicking our logo.'
                },
                {
                    element: '#take-tour-button',
                    title: 'Guided Tour',
                    intro: 'You can restart this tour anytime by clicking this button.'
                },
                {
                    element: '#userDropdown',
                    title: 'User Menu',
                    intro: 'Access your profile settings and log out from this menu.'
                },
                {
                    element: '.landing-hero',
                    title: 'Get Started',
                    intro: 'Click the "Get Started" button to begin your tax filing journey.'
                }
            ],
            showProgress: true,
            showBullets: false,
            hideNext: false,
            hidePrev: false,
            nextLabel: 'Next →',
            prevLabel: '← Back',
            doneLabel: 'Finish Tour'
        });
    } 
    else if (currentPath === '/dashboard') {
        // Dashboard tour
        intro.setOptions({
            steps: [
                {
                    title: 'Your Dashboard',
                    intro: 'This is your tax dashboard where you can track your progress and access all features.'
                },
                {
                    element: '.progress-tracker',
                    title: 'Progress Tracker',
                    intro: 'Track your tax filing progress here. Complete all steps for a successful filing.'
                },
                {
                    element: '.action-cards',
                    title: 'Recommended Actions',
                    intro: 'These cards show the most important actions you should take next.'
                },
                {
                    element: '.document-upload',
                    title: 'Document Upload',
                    intro: 'Upload your tax documents here. Our AI will extract relevant information automatically.'
                },
                {
                    element: '.entity-selection',
                    title: 'Entity Structure',
                    intro: 'Get AI recommendations for the optimal business entity structure based on your situation.'
                },
                {
                    element: '.tax-strategies',
                    title: 'Tax Strategies',
                    intro: 'Discover personalized tax-saving strategies tailored to your business.'
                },
                {
                    element: '.upgrade-tier',
                    title: 'Premium Features',
                    intro: 'Unlock advanced features by upgrading to our Pro tier.'
                }
            ],
            showProgress: true,
            showBullets: false,
            hideNext: false,
            hidePrev: false,
            nextLabel: 'Next →',
            prevLabel: '← Back',
            doneLabel: 'Finish Tour'
        });
    }
    else if (currentPath === '/plans' || currentPath === '/pricing') {
        // Pricing page tour
        intro.setOptions({
            steps: [
                {
                    title: 'Pricing Plans',
                    intro: 'Explore our different pricing tiers to find the one that fits your needs.'
                },
                {
                    element: '.self-service-tier',
                    title: 'Self-Service Tier',
                    intro: 'Our basic tier includes AI-guided tax form completion and PDF export capabilities.'
                },
                {
                    element: '.guided-tier',
                    title: 'Guided Tier',
                    intro: 'Get enhanced AI support, smart form logic, and better tax optimization strategies.'
                },
                {
                    element: '.concierge-tier',
                    title: 'Concierge Tier',
                    intro: 'Our premium tier includes advanced audit protection and AI-powered deduction detection.'
                }
            ],
            showProgress: true,
            showBullets: false,
            hideNext: false,
            hidePrev: false,
            nextLabel: 'Next →',
            prevLabel: '← Back',
            doneLabel: 'Finish Tour'
        });
    }
    
    // Start the tour
    intro.start();
    
    // Track tour completion
    intro.oncomplete(function() {
        console.log('Tour completed');
        // You can add analytics tracking or other actions here
    });
    
    // Track tour exit
    intro.onexit(function() {
        console.log('Tour exited');
        // You can add analytics tracking or other actions here
    });
}

// Initialize tooltips when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Enable all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});