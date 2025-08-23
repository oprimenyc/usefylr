# .fylr Tax Automation Platform

## Overview

.fylr is an AI-powered tax preparation SaaS platform designed for freelancers, microbusinesses, and small business owners. The platform provides automated tax form generation, AI-guided tax strategy recommendations, and tiered pricing based on business complexity. It supports multiple business entity types (Sole Proprietor, LLC, S-Corp, C-Corp) with entity-specific form requirements and tax optimization strategies.

The system is approximately 85% complete for MVP with core infrastructure, enhanced AI tax intelligence, premium React components, form generation, and user management fully implemented. The platform uses advanced entity-specific AI to analyze business data, generate personalized tax strategies with real tax law knowledge, and guide users through complex tax preparation workflows with sophisticated dark theme UI components.

## Recent Changes (August 2025)

### Enhanced AI Tax Intelligence Implementation ✅
- **Entity-Specific Tax Logic**: Implemented sophisticated prompts for sole proprietorship, S-Corp, and LLC analysis
- **Advanced Tax Categorization**: Real tax law knowledge with deduction percentages, audit risk assessment, and IRS guidance
- **Real Tax Calculations**: Actual federal, state, and self-employment tax savings calculations based on current tax brackets
- **Schedule C Line Mapping**: Precise tax form line assignments for each expense category

### Premium React Components with Dark Theme ✅
- **Enhanced Smart Ledger**: Premium glassmorphism design with advanced animations and tax readiness scoring
- **Real-time AI Processing**: Live expense categorization with confidence scoring and documentation requirements
- **Advanced UI/UX**: Professional dark theme with neon orange accents, hover effects, and smooth transitions
- **ROI Indicators**: Real-time return on investment calculations showing platform value versus subscription cost

### Advanced Business Logic Features ✅
- **Smart Upgrade Triggers**: Dynamic subscription prompts based on projected tax savings and usage patterns
- **Audit Risk Assessment**: Color-coded risk indicators (low/medium/high) for each expense category
- **Tax Law Compliance**: Current 2024 tax rates, deduction limits, and IRS guidance integration
- **Documentation Guidance**: Specific receipt and documentation requirements for audit protection

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask-based web application with modular blueprint structure
- **Database**: PostgreSQL with SQLAlchemy ORM for data persistence
- **Authentication**: Flask-Login with user session management and legal disclaimer acknowledgment
- **API Design**: RESTful endpoints organized by functional modules (forms, strategies, billing, etc.)

### AI Integration Layer
- **Primary AI Service**: OpenAI GPT-4o integration for tax strategy analysis and form guidance
- **Prompt Management**: JSON-based prompt templates system for consistent AI interactions
- **AI Modules**: Specialized analyzers for tax strategy, audit risk assessment, and entity optimization
- **Response Processing**: Structured JSON response parsing with error handling and fallback mechanisms

### Form Generation System
- **Dynamic Form Library**: Template-driven form generation with specialized tax field types (EIN, SSN, currency)
- **Form Templates**: JSON-based form definitions for Schedule C, Schedule SE, and other IRS forms
- **Multi-step Navigation**: Progress tracking with session-based form state management
- **Validation Framework**: Field-level validation with conditional logic based on business type and user inputs

### Pricing and Access Control
- **Tiered Pricing Structure**: Three-tier system (Self-Service $97, Guided $197, Concierge $497)
- **Feature Gating**: Access control decorators that restrict features based on subscription level
- **Business Type Eligibility**: Matrix-based access control where S-Corps and C-Corps require higher tiers
- **Upgrade Triggers**: AI-driven upgrade prompts based on business complexity and audit risk factors

### Document Processing
- **File Upload System**: Secure document upload with user-specific folder organization
- **OCR Integration**: Planned integration with AI-powered document analysis for data extraction
- **Export Capabilities**: Multi-format export (PDF, JSON, HTML) for completed forms and strategies

### Business Logic Modules
- **Tax Strategy Engine**: AI-powered analysis of business questionnaires to generate personalized tax optimization recommendations
- **Audit Protection**: Risk assessment algorithms with compliance checking for Pro tier users
- **Entity Recommendation**: AI-driven business structure optimization based on revenue, employees, and tax implications
- **Progress Tracking**: Visual progress indicators with completion status across tax preparation workflow

## External Dependencies

### Core Services
- **OpenAI API**: GPT-4o model for tax strategy analysis, form guidance, and entity optimization recommendations
- **PostgreSQL Database**: Primary data storage for users, forms, strategies, and audit logs
- **Stripe**: Payment processing and subscription management for tiered pricing structure

### Planned Integrations
- **Accounting Software APIs**: QuickBooks Online, Xero, FreshBooks, Wave for automated data import
- **Google Vision API**: Advanced OCR capabilities for document processing and data extraction
- **IRS E-filing Services**: Direct tax return submission capabilities for seamless filing experience

### Infrastructure Dependencies
- **Flask Extensions**: SQLAlchemy, Flask-Login, Flask-WTF for core web application functionality
- **PDF Generation**: ReportLab and WeasyPrint for generating tax forms and strategy reports
- **Document Processing**: PyTesseract and PIL for image-based OCR processing
- **Security**: Werkzeug for password hashing and secure file handling

### Development Tools
- **Database Migrations**: SQLAlchemy migration support for schema updates
- **Session Management**: Flask session handling for multi-step form workflows
- **Error Handling**: Comprehensive logging and error tracking throughout the application
- **Template Engine**: Jinja2 templates with responsive Bootstrap-based UI components