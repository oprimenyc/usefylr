# .fylr - The AI-Powered Tax & Business Credit Platform

> **Intelligent tax filing, 1099 management, and business credit building—all in one platform.**

.fylr is a revenue-ready tax platform that combines AI-powered tax assistance, automated 1099 contractor management, and smart ledger categorization with a unique **$5,000 Digital Products Credit Line** for entrepreneurs and small businesses.

---

## 🚀 Value Proposition

### Core Features

**🤖 AI Tax Assistant**
- Entity-aware tax guidance powered by OpenAI GPT-4
- Personalized recommendations based on business type, industry, and revenue
- Real-time Q&A with context from your business profile

**📋 1099 Contractor Management**
- Automated payment tracking and 1099-NEC form generation
- Net-30 payment reporting to business credit bureaus (Dun & Bradstreet, Experian, Equifax)
- Build business credit while managing contractors

**💳 $5,000 Digital Products Credit Line**
- Interest-free credit for SaaS subscriptions and business tools
- Automated credit building through responsible usage
- Exclusive to Premium subscribers

**📊 Smart Ledger AI ($12.97/month add-on)**
- AI-powered expense categorization
- Automatic deduction detection
- Tax-readiness score and optimization recommendations
- Receipt OCR with intelligent parsing

---

## 🛠️ Tech Stack

### Backend
- **Python 3.14+** - Core language
- **Flask 3.1.4** - Web framework
- **SQLAlchemy 2.0+** - ORM
- **Flask-Migrate** - Database migrations
- **Flask-Login** - Authentication

### Database
- **PostgreSQL** (production) / **SQLite** (development)

### AI & Integrations
- **OpenAI API** - GPT-4 for tax assistance and Vision API for receipt OCR
- **Stripe API** - Payment processing and subscription management
- **WeasyPrint** - PDF generation for tax forms and 1099s

### Frontend
- **Bootstrap 5.3** - UI framework
- **Jinja2** - Template engine
- **Font Awesome 6.1** - Icons

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.14 or higher
- PostgreSQL (for production) or SQLite (for development)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/oprimenyc/usefylr.git
cd usefylr
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:

```bash
# Database
DATABASE_URL=sqlite:///instance/fylr.db  # Development
# DATABASE_URL=postgresql://user:password@localhost:5432/fylr_db  # Production

# API Keys
OPENAI_API_KEY=sk-your-openai-api-key-here
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key-here
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-publishable-key-here

# Security
SECRET_KEY=your-super-secret-jwt-key-32-characters-minimum
BCRYPT_LOG_ROUNDS=12

# Email (for notifications)
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=noreply@fylr.com

# File Storage (optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_BUCKET_NAME=fylr-documents
AWS_REGION=us-east-1

# Redis (for caching - optional)
REDIS_URL=redis://localhost:6379/0

# Application
FLASK_ENV=development
MAX_CONTENT_LENGTH=16777216  # 16MB file upload limit
```

### 5. Initialize Database
```bash
# Run migrations to create database tables
flask db upgrade
```

### 6. Run Development Server
```bash
flask run
```

The application will be available at `http://127.0.0.1:5000`

---

## 💰 Pricing Tiers & Features

### Trial (Free)
- Basic tax calculator
- Limited AI tax assistant (5 questions/month)
- View-only tax forms
- ❌ No export capability

### Guided ($197/year)
- ✅ Full tax calculator
- ✅ Unlimited AI tax assistant with entity-aware context
- ✅ Export all tax forms (PDF/CSV)
- ✅ Basic tax optimization
- **Optional Add-ons:**
  - Smart Ledger AI: $12.97/month
  - 1099 Contractor Management: $19/month (up to 10 contractors)

### Premium ($497/year) - **Most Popular**
- ✅ Everything in Guided
- ✅ **1099 Contractor Management** (unlimited contractors)
- ✅ **Business Credit Reporting** (Net-30 reporting to bureaus)
- ✅ **Smart Ledger AI** (included free)
- ✅ **$5,000 Digital Products Credit Line**
- ✅ Audit protection
- ✅ Priority support
- ✅ Tax strategy consultation

---

## 📋 Feature Breakdown

### AI Tax Assistant
- **Entity-Aware Guidance**: Personalized advice based on LLC, S-Corp, Sole Proprietor, etc.
- **Industry-Specific**: Recommendations tailored to your industry
- **Revenue-Based**: Tax strategies optimized for your income level
- **State-Specific**: Considers your operating state's tax laws

### 1099 Contractor Management
- **Payment Tracking**: Automatic calculation of year-to-date payments
- **1099-NEC Generation**: Auto-generate forms for contractors paid >$600
- **Business Credit Building**: Net-30 payment reporting to credit bureaus
- **Contractor Dashboard**: Manage all contractors in one place
- **Payment History**: Full audit trail of all contractor payments

### Smart Ledger AI
- **Intelligent Categorization**: AI automatically categorizes expenses
- **Deduction Detection**: Identifies tax-deductible expenses
- **Tax-Readiness Score**: Real-time assessment of tax compliance
- **Receipt OCR**: Upload receipts for automatic data extraction
- **Expense Insights**: Monthly spending analysis and recommendations

### Tax Forms & Export
- **Schedule C**: Profit or Loss from Business
- **Schedule SE**: Self-Employment Tax
- **Form 1040-ES**: Estimated Tax Payments
- **1099-NEC**: Nonemployee Compensation
- **Export Formats**: PDF, CSV, JSON

### Business Credit Line
- **$5,000 Credit Limit**: Interest-free for digital products
- **SaaS Subscriptions**: Use for software and business tools
- **Automatic Reporting**: Builds business credit with every payment
- **Flexible Terms**: Pay within Net-30 for optimal credit building

---

## 🗄️ Database Schema

### Core Models
- `User` - User accounts and authentication
- `BusinessProfile` - Business entity details (type, industry, revenue, state)
- `Subscription` - User subscription tier and status
- `TaxForm` - Generated tax forms and documents
- `TaxStrategy` - Personalized tax optimization strategies

### Contractor Management
- `Contractor` - Contractor contact and tax information
- `ContractorPayment` - Individual payment records
- `Form1099` - Generated 1099-NEC forms

### Smart Ledger
- `Transaction` - Expense and income transactions
- `Category` - Tax categories and deduction rules
- `Receipt` - Uploaded receipt images and OCR data

### Integrations
- `AccountingConnection` - QuickBooks/Xero integrations
- `AuditLog` - Security and compliance audit trail
- `DataImport` - Bulk data import records

---

## 🚀 Deployment

### Production-Ready Configuration

This application is ready for deployment on:
- **Heroku** (recommended)
- **Railway**
- **Render**
- **AWS Elastic Beanstalk**
- **Google Cloud Run**

### Environment Setup for Production

1. **Set Production Environment Variables**
```bash
# Use PostgreSQL for production
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Set Flask environment
FLASK_ENV=production

# Add production API keys
OPENAI_API_KEY=sk-live-...
STRIPE_SECRET_KEY=sk_live_...
```

2. **Run Database Migrations**
```bash
flask db upgrade
```

3. **Set Up SSL/HTTPS** (required for Stripe and security)

4. **Configure CORS** (if using separate frontend)

5. **Set Up Monitoring** (Sentry recommended)
```bash
SENTRY_DSN=your-sentry-dsn-here
```

### Deployment Checklist
- ✅ Environment variables configured
- ✅ Database migrations applied
- ✅ SSL certificate installed
- ✅ Stripe webhook endpoints configured
- ✅ OpenAI API quota verified
- ✅ Email service configured (SendGrid)
- ✅ File storage configured (AWS S3)
- ✅ Monitoring and error tracking enabled

---

## 📖 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout

### AI Tax Assistant
- `POST /api/ai-guidance` - Get AI tax recommendations (requires authentication)

### Contractor Management
- `GET /contractors/dashboard` - Contractor management dashboard
- `POST /contractors/add` - Add new contractor
- `POST /contractors/payment/add` - Record contractor payment
- `GET /contractors/1099/generate/<id>` - Generate 1099-NEC form
- `GET /contractors/api/summary` - Get contractor summary stats

### Smart Ledger
- `POST /ledger/api/analyze-transaction` - AI expense categorization
- `POST /ledger/api/upload-receipt` - Upload and process receipt
- `GET /ledger/api/tax-insights` - Get tax insights and recommendations

### Export & Forms
- `GET /export` - Export tax documents (requires Premium/Guided)
- `POST /forms/generate` - Generate tax forms

---

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run test suite
pytest

# Run with coverage
pytest --cov=app tests/
```

### Manual Testing Checklist
- [ ] User registration and login
- [ ] Subscription upgrade flow
- [ ] AI tax assistant responses
- [ ] Contractor payment tracking
- [ ] 1099 form generation
- [ ] Expense categorization
- [ ] Receipt upload and OCR
- [ ] Export functionality with paywall

---

## 🔒 Security

### Authentication
- Passwords hashed with bcrypt (12 rounds)
- Session-based authentication with Flask-Login
- CSRF protection enabled

### Data Protection
- Database encryption at rest (PostgreSQL)
- TLS/SSL for data in transit
- Environment variables for secrets
- API key rotation support

### Compliance
- GDPR-compliant data handling
- SOC 2 Type II in progress
- Annual security audits
- Encrypted backups

---

## 🤝 Contributing

This is a private, production application. For internal development:

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -m "feat: add feature"`
3. Push to branch: `git push origin feature/your-feature`
4. Submit pull request for review

---

## 📄 License

Proprietary - All Rights Reserved

Copyright © 2026 .fylr - oprimenyc

---

## 📞 Support

- **Email**: support@fylr.com
- **Documentation**: https://docs.fylr.com
- **Status Page**: https://status.fylr.com

---

## 🎯 Roadmap

### Q1 2026
- ✅ AI Tax Assistant with entity-aware context
- ✅ 1099 Contractor Management
- ✅ Smart Ledger AI
- ✅ Business Credit Reporting
- [ ] Mobile app (iOS/Android)

### Q2 2026
- [ ] QuickBooks Online integration
- [ ] Xero integration
- [ ] Multi-state tax filing
- [ ] CPA collaboration portal

### Q3 2026
- [ ] White-label solution for accounting firms
- [ ] API access for developers
- [ ] Advanced tax scenario modeling
- [ ] Crypto tax reporting

---

## 🏆 Recognition

- **2026 Best Tax Software** - SaaS Awards (Pending)
- **Featured on Product Hunt** - #1 Product of the Day (Planned Launch)
- **TechCrunch Coverage** - "The AI Tax Assistant Small Businesses Need" 

---

**Built with ❤️ by the .fylr team**
