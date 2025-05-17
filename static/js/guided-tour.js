// Guided Tour for .fylr Tax Platform
document.addEventListener('DOMContentLoaded', function() {
  // Check if this is the user's first visit or if they explicitly requested the tour
  const shouldShowTour = localStorage.getItem('fylr_tour_completed') !== 'true' || 
                         window.location.search.includes('tour=true');
  
  if (shouldShowTour) {
    startGuidedTour();
  }
  
  // Add an event listener to the "Take Tour" button if it exists
  const tourButton = document.getElementById('take-tour-button');
  if (tourButton) {
    tourButton.addEventListener('click', startGuidedTour);
  }
});

function startGuidedTour() {
  // Initialize introJs
  const tour = introJs();
  
  // Configure the tour
  tour.setOption('dontShowAgain', true);
  tour.setOption('overlayOpacity', 0.7);
  tour.setOption('showProgress', true);
  tour.setOption('showBullets', true);
  tour.setOption('scrollToElement', true);
  tour.setOption('tooltipClass', 'fylr-tooltip');
  tour.setOption('highlightClass', 'fylr-highlight');
  tour.setOption('exitOnOverlayClick', false);
  
  // Define the tour steps
  // These steps will be customized based on which page the user is on
  
  const currentPath = window.location.pathname;
  
  // Define different tour steps for different pages
  if (currentPath === '/dashboard') {
    // Dashboard tour
    tour.setSteps([
      {
        element: '.dashboard-overview',
        intro: 'Welcome to your .fylr dashboard! This is your command center for tax preparation.',
        position: 'right'
      },
      {
        element: '.progress-tracker',
        intro: 'Track your tax preparation progress here. The platform will guide you through each step.',
        position: 'bottom'
      },
      {
        element: '.action-cards',
        intro: 'These cards show recommended actions to complete your tax preparation.',
        position: 'left'
      },
      {
        element: '.entity-selection',
        intro: 'Our AI will recommend the optimal entity structure for your business. Click here to explore options.',
        position: 'top'
      },
      {
        element: '.document-upload',
        intro: 'Upload your documents here. Our AI will automatically extract relevant tax information.',
        position: 'bottom'
      },
      {
        element: '.tax-strategies',
        intro: 'Access personalized tax strategies based on your business profile and questionnaire responses.',
        position: 'left'
      },
      {
        element: '.upgrade-tier',
        intro: 'Unlock more features by upgrading to Plus or Pro tiers, including enhanced AI analysis and audit protection.',
        position: 'left'
      }
    ]);
  } else if (currentPath === '/documents') {
    // Documents tour
    tour.setSteps([
      {
        element: '.document-upload-area',
        intro: 'Upload your tax documents here. We support various formats including PDFs and images.',
        position: 'right'
      },
      {
        element: '.document-categories',
        intro: 'Documents are organized into these categories for easy access.',
        position: 'left'
      },
      {
        element: '.ai-extraction',
        intro: 'Our AI automatically extracts key information from your documents, saving you time on data entry.',
        position: 'bottom'
      },
      {
        element: '.document-table',
        intro: 'View all your uploaded documents here. Click on any document to see the extracted information.',
        position: 'top'
      }
    ]);
  } else if (currentPath === '/entity') {
    // Entity recommendation tour
    tour.setSteps([
      {
        element: '.entity-questionnaire',
        intro: 'Answer these questions to help our AI recommend the optimal entity structure for your business.',
        position: 'right'
      },
      {
        element: '.entity-recommendation',
        intro: 'Based on your answers, we\'ll provide a detailed recommendation with pros and cons of each entity type.',
        position: 'left'
      },
      {
        element: '.entity-comparison',
        intro: 'Compare different entity types side-by-side to make the best decision for your business.',
        position: 'bottom'
      }
    ]);
  } else if (currentPath === '/audit') {
    // Audit protection tour
    tour.setSteps([
      {
        element: '.risk-assessment',
        intro: 'Our AI analyzes your business profile to identify potential audit triggers.',
        position: 'right'
      },
      {
        element: '.document-organizer',
        intro: 'Keep your tax documents organized and audit-ready with our document management system.',
        position: 'left'
      },
      {
        element: '.compliance-check',
        intro: 'Run automated compliance checks to ensure your tax forms are accurate and complete.',
        position: 'bottom'
      }
    ]);
  } else {
    // Default homepage tour
    tour.setSteps([
      {
        element: '.welcome-section',
        intro: 'Welcome to .fylr! We use AI to simplify your business tax preparation.',
        position: 'bottom'
      },
      {
        element: '.main-features',
        intro: 'Our platform offers document scanning, entity recommendations, tax strategies, and more.',
        position: 'right'
      },
      {
        element: '.pricing-section',
        intro: 'Choose from three tiers: Basic, Plus, and Pro, each with different features to meet your needs.',
        position: 'left'
      },
      {
        element: '.signup-section',
        intro: 'Get started by creating an account or logging in if you already have one.',
        position: 'bottom'
      }
    ]);
  }
  
  // Start the tour
  tour.start();
  
  // Track when the tour is completed
  tour.oncomplete(function() {
    localStorage.setItem('fylr_tour_completed', 'true');
  });
  
  // Track when the tour is exited
  tour.onexit(function() {
    // We still mark it as completed even if they exit early
    localStorage.setItem('fylr_tour_completed', 'true');
  });
}

// Function to manually trigger the tour from anywhere
function showGuidedTour() {
  startGuidedTour();
}