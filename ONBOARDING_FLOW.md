# Onboarding Flow Documentation

## Overview

The smart onboarding flow demonstrates AI value BEFORE requiring user registration. This "try before you buy" approach increases conversion rates by showing immediate value.

## User Journey

### 1. Entry Points

**Get Started Button** → `/onboarding`
- Header navigation (unauthenticated users)
- Landing page hero button
- Pricing page CTAs

### 2. Welcome Screen (`/onboarding`)

**Glass Card Experience:**
- Welcoming headline: "See Your Tax Savings in Seconds"
- Subheadline explaining no signup required
- **Buy Box** - AI expense input field
- Example placeholder: "I bought a $3,000 laptop for my business"
- Feature highlights (Instant Analysis, IRS Compliant, Maximize Deductions)

### 3. Try AI Demo (No Registration Required)

**User Action:**
1. Types natural language expense description
2. Clicks "Analyze with AI" button

**Backend Processing:**
- POST to `/onboarding/try-ai`
- Parses expense using Dynamic Tax Engine
- Returns structured tax data as JSON
- Stores demo usage in session

**Frontend Display:**
- Result card animates in with glass morphism design
- Shows:
  - IRS Category
  - Dollar Amount
  - IRS Guidance
  - Schedule C Line
  - Deductible Percentage
  - Audit Risk Level
  - AI Confidence Score

### 4. The Hook

**After First Demo:**
- Green signup prompt card appears
- Headline: "Ready to save thousands on your taxes?"
- Value proposition: Track all expenses, get complete tax package
- **Primary CTA:** "Create Free Account" → `/onboarding/get-started`
- **Secondary:** "Skip for now" link

### 5. Progressive Signup

**Route:** `/onboarding/get-started`
- Sets session flag: `return_to_onboarding = true`
- Redirects to `/register?source=onboarding`
- Signup form can use demo data from session
- After registration, returns to dashboard with demo expenses pre-loaded

## State Management

### Session Variables

```python
# Tracked in onboarding flow
session['onboarding_started'] = True
session['demo_expenses'] = [
    {
        'description': '...',
        'amount': 2500.0,
        'category': 'Section 179 Equipment Deduction'
    }
]
session['return_to_onboarding'] = True
session['onboarding_skipped'] = True
```

### Authentication Check

**In Header (`beautiful_base.html`):**
```jinja
{% if current_user.is_authenticated %}
    <!-- Show: Dashboard button, User status, Logout -->
{% else %}
    <!-- Show: Get Started → /onboarding, Sign In -->
{% endif %}
```

**In Onboarding Route:**
```python
if current_user.is_authenticated:
    return redirect(url_for('main.dashboard'))
```

## API Endpoints

### POST `/onboarding/try-ai`

**Purpose:** Let anonymous users test AI without registration

**Request:**
```json
{
  "description": "I bought a laptop for 2500 dollars"
}
```

**Response:**
```json
{
  "success": true,
  "expense": {
    "amount": 2500.0,
    "irs_category": "Section 179 Equipment Deduction",
    "schedule_c_line": 13,
    "deduction_percentage": 100,
    "audit_risk": "low",
    "confidence": 0.7,
    "irs_guidance": "Equipment over $2,500 may qualify..."
  },
  "show_signup_prompt": true
}
```

### GET `/onboarding/get-started`

**Purpose:** Continue to signup with context

**Flow:**
1. Sets session flag
2. Redirects to `/register?source=onboarding`
3. Registration form shows personalized messaging
4. After signup, pre-loads demo expenses into user account

### GET `/onboarding/skip`

**Purpose:** Skip onboarding, go straight to signup

**Flow:**
1. Sets `onboarding_skipped = true`
2. Redirects to `/register`

## Visual Design

### Glass Morphism Cards

**Welcome Card:**
- Background: `linear-gradient(135deg, rgba(17,17,17,0.9) 0%, rgba(17,17,17,0.6) 100%)`
- Backdrop filter: `blur(20px)`
- Border: `1px solid rgba(255,255,255,0.1)`
- Border radius: `24px` (var(--radius-2xl))
- Top border gradient glow in orange

**Result Card:**
- Background: `linear-gradient(135deg, rgba(255,107,0,0.1) 0%, rgba(255,107,0,0.05) 100%)`
- Border: `1px solid rgba(255,107,0,0.3)`
- Slide-in animation
- Grid layout for details
- Color-coded audit risk (green/yellow/red)

**Signup Prompt Card:**
- Background: `linear-gradient(135deg, rgba(0,208,132,0.1) 0%, rgba(0,150,100,0.1) 100%)`
- Border: `1px solid rgba(0,208,132,0.3)`
- Green theme to signal positive action
- Slide-in animation after first demo

### Animations

**Slide In:**
```css
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

**Loading Spinner:**
- Inline spinner on button during API call
- Prevents duplicate submissions
- Button text changes: "Analyze with AI" → "Analyzing..." → "Try Another Expense"

## No Dead Ends

**Every step has a clear next action:**

1. **Landing Page** → "Get Started" button
2. **Onboarding Welcome** → Try AI demo
3. **After Demo** → Create Account or Try Another
4. **Signup** → Dashboard with pre-loaded data
5. **Dashboard** → Continue with expenses

**Progressive Disclosure:**
- First: Show value (AI demo)
- Then: Ask for commitment (registration)
- Finally: Deliver product (full platform)

## Header Logic

### Unauthenticated Users

**Navigation:**
- Home
- AI Questionnaire
- AI Chat
- Pricing

**Right Side:**
- **Get Started** (orange CTA) → `/onboarding`
- **Sign In** (text link) → `/login`

### Authenticated Users

**Navigation:**
- Home
- Smart Ledger
- AI Questionnaire
- AI Chat
- Dashboard (authenticated only)
- 1099 Management (authenticated only)
- Pricing

**Right Side:**
- User Status (subscription tier + email)
- **Dashboard** (orange CTA) → `/dashboard`
- **Logout** (text link) → `/logout`

## Conversion Optimization

### Psychological Triggers

1. **Instant Gratification:** See results immediately
2. **No Risk:** Try before registering
3. **Social Proof:** "AI-powered" builds trust
4. **Urgency:** "Ready to save thousands?"
5. **Clear Value:** Shows exact deduction amounts

### Copy Strategy

**Before Demo:**
- "See Your Tax Savings in Seconds"
- "Try it now — no signup required"

**After Demo:**
- "Ready to save thousands on your taxes?"
- "Create a free account to track all your expenses"

### A/B Test Ideas

- Variation 1: Pre-fill example expense
- Variation 2: Show dollar amount saved immediately
- Variation 3: Add testimonial after demo
- Variation 4: Gamify with "Track 5 more expenses to unlock analysis"

## Technical Implementation

### Files Created

1. `app/onboarding.py` - Onboarding blueprint with routes
2. `templates/onboarding/welcome.html` - Welcome screen template
3. `ONBOARDING_FLOW.md` - This documentation

### Files Modified

1. `app/__init__.py` - Registered onboarding_bp
2. `templates/beautiful_base.html` - Updated header buttons
3. `templates/index.html` - Updated hero CTA

### Dependencies

- Dynamic Tax Engine (`app/modules/intake.py`)
- Session management (Flask sessions)
- Authentication (Flask-Login)

## Testing

### Manual Test Flow

1. Open browser to `http://localhost:5000`
2. Click "Get Started" → Should go to `/onboarding`
3. Type "I bought a laptop for 3000" in input
4. Click "Analyze with AI"
5. Verify result card shows:
   - Section 179 Equipment Deduction
   - $3,000 amount
   - Line 13
   - Low audit risk
6. Verify signup prompt appears
7. Click "Create Free Account" → Should go to `/register?source=onboarding`

### API Test

```bash
curl -X POST http://localhost:5000/onboarding/try-ai \
  -H "Content-Type: application/json" \
  -d '{"description": "I bought a laptop for 2500 dollars"}'
```

**Expected Response:**
```json
{
  "success": true,
  "expense": {
    "amount": 2500.0,
    "irs_category": "Section 179 Equipment Deduction",
    ...
  },
  "show_signup_prompt": true
}
```

## Future Enhancements

1. **Email Capture:** Ask for email before demo to follow up
2. **Multi-Expense Demo:** Let users try 3-5 expenses before signup
3. **Savings Calculator:** Show total annual savings projection
4. **Industry Detection:** Auto-detect business type from expenses
5. **Personalized Messaging:** Tailor signup copy based on demo usage
6. **Exit Intent:** Show special offer when user tries to leave
7. **Social Sharing:** "I just saved $X on my taxes with .fylr"

## Analytics to Track

- Onboarding page views
- Demo usage rate (% who try AI)
- Average demos per session
- Conversion rate (demo → signup)
- Time to first demo
- Drop-off points in funnel

## Error Handling

**If API Fails:**
- Show friendly error message
- Don't lose user input
- Allow retry
- Fallback to contact form

**If No Amount Detected:**
- Still show category and guidance
- Suggest user add explicit dollar amount
- Show example format

**If Session Expires:**
- Gracefully handle session loss
- Don't require re-entry of data
- Auto-save demo to localStorage as backup
