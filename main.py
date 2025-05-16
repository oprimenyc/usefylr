from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>.fylr - AI-Powered Tax Automation</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css">
        <style>
            :root {
                --fylr-orange: #FF6B00;
            }
            .btn-fylr {
                background-color: var(--fylr-orange);
                border-color: var(--fylr-orange);
                color: white;
            }
            .text-fylr {
                color: var(--fylr-orange);
            }
            .hero {
                background: linear-gradient(135deg, #FF6B00 0%, #FF9E00 100%);
                color: white;
                padding: 100px 0;
            }
        </style>
    </head>
    <body>
        <!-- Hero Section -->
        <section class="hero">
            <div class="container text-center">
                <h1 class="display-4 fw-bold mb-4">.fylr - AI-Powered Tax Automation</h1>
                <p class="lead mb-5">Simplify your business tax preparation with AI assistance. <br>No tax expertise required.</p>
                <div class="d-grid gap-2 d-sm-flex justify-content-sm-center">
                    <a href="/plans" class="btn btn-light btn-lg px-4 gap-3">View Plans</a>
                    <a href="#features" class="btn btn-outline-light btn-lg px-4">Learn More</a>
                </div>
            </div>
        </section>

        <!-- Key Features -->
        <section class="py-5" id="features">
            <div class="container">
                <h2 class="text-center mb-5">Why Choose .fylr?</h2>
                
                <div class="row">
                    <div class="col-md-4 mb-4">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-robot fs-1 text-fylr mb-3"></i>
                                <h3 class="fs-5">AI-Guided Experience</h3>
                                <p>Our AI guides you through the entire tax preparation process.</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4 mb-4">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-file-invoice-dollar fs-1 text-fylr mb-3"></i>
                                <h3 class="fs-5">Smart Tax Forms</h3>
                                <p>Automatically select and fill the right tax forms based on your business.</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4 mb-4">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-search-dollar fs-1 text-fylr mb-3"></i>
                                <h3 class="fs-5">Deduction Detection</h3>
                                <p>AI-powered analysis finds potential deductions you might miss.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Footer -->
        <footer class="py-4 bg-dark text-white">
            <div class="container">
                <div class="row">
                    <div class="col-md-6 text-center text-md-start">
                        <p class="mb-0">&copy; 2025 .fylr. All rights reserved.</p>
                    </div>
                    <div class="col-md-6 text-center text-md-end">
                        <p class="small text-muted mb-0">DISCLAIMER: This tool is provided for informational purposes only.</p>
                    </div>
                </div>
            </div>
        </footer>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

@app.route('/plans')
def plans():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Plans - .fylr Tax Automation</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css">
        <style>
            :root {
                --fylr-orange: #FF6B00;
            }
            .btn-fylr {
                background-color: var(--fylr-orange);
                border-color: var(--fylr-orange);
                color: white;
            }
            .text-fylr {
                color: var(--fylr-orange);
            }
            .bg-fylr {
                background-color: var(--fylr-orange);
            }
            .page-header {
                background: linear-gradient(135deg, #FF6B00 0%, #FF9E00 100%);
                color: white;
                padding: 50px 0;
            }
        </style>
    </head>
    <body>
        <!-- Header -->
        <header class="page-header">
            <div class="container text-center">
                <h1 class="display-4 fw-bold mb-4">Pricing Plans</h1>
                <p class="lead">Choose the right plan for your business needs</p>
            </div>
        </header>

        <!-- Plans Section -->
        <section class="py-5">
            <div class="container">
                <div class="row g-4">
                    <div class="col-md-4">
                        <div class="card h-100 shadow-sm">
                            <div class="card-header bg-dark text-white text-center py-3">
                                <h3 class="fs-5 mb-0">Self-Service</h3>
                            </div>
                            <div class="card-body d-flex flex-column">
                                <div class="mb-4 text-center">
                                    <span class="display-6">$97</span>
                                </div>
                                <ul class="list-unstyled mb-4">
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> Auto-fill IRS forms</li>
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> Smart document upload</li>
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> AI assistance</li>
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> Download-ready PDFs</li>
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> Basic error check</li>
                                </ul>
                                <a href="#" class="btn btn-outline-dark mt-auto">Get Started</a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="card h-100 shadow">
                            <div class="card-header bg-fylr text-white text-center py-3">
                                <h3 class="fs-5 mb-0">Guided</h3>
                                <span class="badge bg-white text-fylr">POPULAR</span>
                            </div>
                            <div class="card-body d-flex flex-column">
                                <div class="mb-4 text-center">
                                    <span class="display-6">$197</span>
                                </div>
                                <ul class="list-unstyled mb-4">
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> Everything in Self-Service</li>
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> AI tax strategy recommendations</li>
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> Smart deduction alerts</li>
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> Compliance warnings</li>
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> Year-end closing guidance</li>
                                </ul>
                                <a href="#" class="btn btn-fylr mt-auto">Get Started</a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="card h-100 shadow-sm">
                            <div class="card-header bg-dark text-white text-center py-3">
                                <h3 class="fs-5 mb-0">Concierge</h3>
                            </div>
                            <div class="card-body d-flex flex-column">
                                <div class="mb-4 text-center">
                                    <span class="display-6">$497</span>
                                </div>
                                <ul class="list-unstyled mb-4">
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> Everything in Guided</li>
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> Automated document collection</li>
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> AI-reviewed tax package</li>
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> Lifetime digital backup</li>
                                    <li class="mb-2"><i class="fas fa-check text-success me-2"></i> Audit protection included</li>
                                </ul>
                                <a href="#" class="btn btn-outline-dark mt-auto">Get Started</a>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="mt-5 pt-5 text-center">
                    <a href="/" class="btn btn-primary">Back to Home</a>
                </div>
            </div>
        </section>

        <!-- Footer -->
        <footer class="py-4 bg-dark text-white">
            <div class="container">
                <div class="row">
                    <div class="col-md-6 text-center text-md-start">
                        <p class="mb-0">&copy; 2025 .fylr. All rights reserved.</p>
                    </div>
                    <div class="col-md-6 text-center text-md-end">
                        <p class="small text-muted mb-0">DISCLAIMER: This tool is provided for informational purposes only.</p>
                    </div>
                </div>
            </div>
        </footer>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)