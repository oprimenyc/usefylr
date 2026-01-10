# Dynamic Tax Engine API Documentation

## Overview

The Intake API provides AI-powered parsing of natural language expense descriptions into structured tax data. It supports contextual parsing, complexity assessment, and startup cost optimization.

## Base URL

```
http://localhost:5000/api/intake
```

## Endpoints

### 1. Parse Expense

Parse a natural language expense description into structured tax data.

**Endpoint:** `POST /api/intake/parse-expense`

**Request Body:**
```json
{
  "description": "I bought a laptop for $3,000",
  "amount": 3000  // Optional if amount is in description
}
```

**Response:**
```json
{
  "success": true,
  "expense": {
    "description": "I bought a laptop for $3,000",
    "amount": 3000.0,
    "irs_category": "Section 179 Equipment Deduction",
    "schedule_c_line": 13,
    "schedule_c_description": "Depreciation and section 179 expense deduction",
    "category_key": "depreciation",
    "deduction_percentage": 100,
    "is_startup_cost": false,
    "requires_documentation": true,
    "audit_risk": "low",
    "irs_guidance": "Equipment over $2,500 may qualify for Section 179...",
    "confidence": 0.95
  }
}
```

**Use Case - Update Glass Card:**
```javascript
// Frontend JavaScript example
async function addExpense(description) {
  const response = await fetch('/api/intake/parse-expense', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ description })
  });

  const data = await response.json();

  if (data.success) {
    // Update glass card without page reload
    updateGlassCard(data.expense);
    addToTotalDeductions(data.expense.amount);
    showScheduleCLine(data.expense.schedule_c_line);
  }
}
```

---

### 2. Assess Complexity

Analyze business complexity based on expenses and profile to determine if advanced questionnaire modules are needed.

**Endpoint:** `POST /api/intake/assess-complexity`

**Request Body:**
```json
{
  "expense_descriptions": [
    "Hired 3 employees this year",
    "Bought inventory from overseas",
    "Paid quarterly taxes"
  ],
  "business_profile": {
    "has_employees": true,
    "has_inventory": true,
    "annual_revenue": 350000
  }
}
```

**Response:**
```json
{
  "complexity_level": "high",
  "complexity_score": 50,
  "flags": [
    {
      "trigger": "employee",
      "category": "Payroll & Employment",
      "recommendation": "Enable Form 941 (Quarterly Payroll Tax)..."
    }
  ],
  "requires_advanced_questionnaire": true,
  "recommended_tier": "premium",
  "estimated_forms": ["Schedule C", "Form 941", "Form 940", "W-2", "W-3"]
}
```

**Complexity Triggers:**
- `employees`, `payroll`, `w-2` → Payroll & Employment complexity
- `foreign`, `international`, `overseas` → International Tax complexity
- `inventory`, `stock`, `merchandise` → Inventory Accounting complexity
- `cryptocurrency`, `crypto`, `bitcoin` → Digital Assets complexity
- `partnership`, `s-corp` → Complex Entity Structure

**Use Case - Dynamic Questionnaire Flow:**
```javascript
async function determineQuestionnairePath(expenses, profile) {
  const response = await fetch('/api/intake/assess-complexity', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      expense_descriptions: expenses,
      business_profile: profile
    })
  });

  const data = await response.json();

  if (data.complexity_level === 'high') {
    // Trigger advanced modules
    enablePayrollModule();
    enableInventoryTracking();
    recommendPremiumTier();
  }
}
```

---

### 3. Optimize Startup Costs (Loss-Leader Strategy)

Analyze startup costs for businesses with $0 revenue to maximize first-year deductions.

**Endpoint:** `POST /api/intake/optimize-startup`

**Request Body:**
```json
{
  "expenses": [
    {
      "description": "LLC formation fees",
      "amount": 800,
      "is_startup_cost": true
    },
    {
      "description": "Initial website development",
      "amount": 3500,
      "is_startup_cost": true
    }
  ],
  "revenue": 0
}
```

**Response:**
```json
{
  "total_startup_costs": 4300.0,
  "immediate_deduction": 4300.0,
  "amortizable_amount": 0.0,
  "monthly_amortization": 0.0,
  "first_year_total_deduction": 4300.0,
  "strategy": "loss-leader",
  "irs_form": "Form 4562 (Depreciation and Amortization)",
  "recommendations": [
    "💡 Your startup costs of $4,300 will create a $4,300 business loss...",
    "📋 File Schedule C even with $0 revenue to claim your startup deductions.",
    "🎯 This loss can reduce your overall tax liability if you have other income..."
  ]
}
```

**Startup Cost Keywords:**
- `startup`, `start-up`, `initial`, `formation`
- `incorporation`, `llc filing`, `organizational costs`
- `pre-opening`, `launch`

**IRS Rules Applied:**
- Up to $5,000 in startup costs can be deducted in Year 1
- Excess is amortized over 180 months (15 years)
- First-year amortization calculated for partial year

---

### 4. Batch Parse (Authenticated)

Parse multiple expenses at once for logged-in users.

**Endpoint:** `POST /api/intake/batch-parse`

**Authentication:** Required (login_required)

**Request Body:**
```json
{
  "expenses": [
    { "description": "Bought laptop $2500" },
    { "description": "Office rent $1200/month" },
    { "description": "Hired accountant $500" }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "parsed_expenses": [...],
  "summary": {
    "total_count": 3,
    "total_amount": 4200.0,
    "by_category": {
      "depreciation": { "count": 1, "total": 2500.0 },
      "rent_lease_property": { "count": 1, "total": 1200.0 },
      "legal_professional": { "count": 1, "total": 500.0 }
    }
  }
}
```

---

## Schedule C Line Mappings

The API maps expenses to the correct Schedule C (Form 1040) lines:

| Line | Description | Example Expenses |
|------|-------------|------------------|
| 8 | Advertising | Google Ads, Facebook Marketing |
| 9 | Car and truck expenses | Mileage, Gas, Maintenance |
| 13 | Depreciation and Section 179 | Equipment, Computers, Furniture |
| 15 | Insurance | Business Insurance, Liability |
| 17 | Legal and professional services | Lawyers, Accountants, Consultants |
| 18 | Office expense | Supplies, Software, Subscriptions |
| 20 | Rent or lease | Office Rent, Equipment Lease |
| 24 | Travel and meals | Flights, Hotels, Business Meals (50%) |
| 25 | Utilities | Internet, Phone, Electricity |
| 27 | Other expenses | Miscellaneous Business Expenses |

---

## AI Classification

The system uses a hybrid approach:

### With Anthropic API Key

If `ANTHROPIC_API_KEY` is set in environment variables, the system uses Claude AI for advanced classification with higher confidence scores.

### Fallback Mode (No API Key)

Uses keyword-based pattern matching with predefined rules. Still provides accurate classifications for common expenses.

**To enable AI mode:**
```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

---

## Frontend Integration Examples

### React Example - Buy Box Integration

```javascript
import React, { useState } from 'react';

function ExpenseInput() {
  const [description, setDescription] = useState('');
  const [expense, setExpense] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const response = await fetch('/api/intake/parse-expense', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description })
    });

    const data = await response.json();
    if (data.success) {
      setExpense(data.expense);
      // Update glass card without reload
      animateGlassCard(data.expense);
    }
  };

  return (
    <div className="glass-card p-4">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What did you buy? (e.g., 'I bought a $3k laptop')"
          className="enhanced-input"
        />
        <button type="submit" className="ai-analyze-button">
          Analyze with AI
        </button>
      </form>

      {expense && (
        <div className="expense-result">
          <h4>{expense.irs_category}</h4>
          <p>Schedule C Line {expense.schedule_c_line}</p>
          <p className="text-success">${expense.amount} deduction</p>
          <small>{expense.irs_guidance}</small>
        </div>
      )}
    </div>
  );
}
```

### Vanilla JavaScript - Progressive Enhancement

```javascript
// Enhance existing Buy Box form
document.getElementById('buy-box-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const description = e.target.description.value;

  // Show loading state
  showLoadingSpinner();

  try {
    const response = await fetch('/api/intake/parse-expense', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description })
    });

    const data = await response.json();

    if (data.success) {
      // Update glass card dynamically
      updateExpenseCard({
        amount: data.expense.amount,
        category: data.expense.irs_category,
        line: data.expense.schedule_c_line,
        deduction: data.expense.deduction_percentage,
        guidance: data.expense.irs_guidance
      });

      // Animate the update
      animateNewExpense();
    }
  } catch (error) {
    showError('Failed to process expense');
  } finally {
    hideLoadingSpinner();
  }
});
```

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message here"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (missing required fields)
- `401` - Unauthorized (batch-parse only)
- `500` - Server Error

---

## Health Check

**Endpoint:** `GET /api/intake/health`

**Response:**
```json
{
  "status": "healthy",
  "service": "intake-api",
  "version": "1.0.0"
}
```

---

## Testing

### Manual Testing with curl

```bash
# Test parse-expense
curl -X POST http://localhost:5000/api/intake/parse-expense \
  -H "Content-Type: application/json" \
  -d '{"description": "I bought a laptop for 3000 dollars"}'

# Test assess-complexity
curl -X POST http://localhost:5000/api/intake/assess-complexity \
  -H "Content-Type: application/json" \
  -d '{"expense_descriptions": ["Hired employees"], "business_profile": {"has_employees": true}}'

# Test optimize-startup
curl -X POST http://localhost:5000/api/intake/optimize-startup \
  -H "Content-Type: application/json" \
  -d '{"expenses": [{"amount": 5000, "is_startup_cost": true}], "revenue": 0}'
```

### Python Testing

```python
from app.modules.intake import parse_expense_string

# Test directly
result = parse_expense_string("I bought a $3k laptop")
print(result['expense']['irs_category'])
# Output: Section 179 Equipment Deduction
```

---

## Performance Notes

- **Parse Expense**: ~100-500ms (depends on AI mode)
- **Assess Complexity**: ~50-100ms
- **Optimize Startup**: ~10-50ms
- **Batch Parse**: ~200ms per expense

## Security

- All endpoints accept JSON only
- Input sanitization applied
- Rate limiting recommended for production
- Authentication required for batch operations

---

## Next Steps

1. Add frontend Buy Box integration
2. Configure Anthropic API key for AI mode
3. Implement glass card animations
4. Add expense history tracking
5. Build advanced questionnaire modules
