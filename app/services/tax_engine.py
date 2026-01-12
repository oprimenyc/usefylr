"""
Tax Engine Service - Centralized 2026 Tax Code Logic

This module provides professional tax calculation services based on IRS tax rules,
including standard deductions, tax brackets, and business deduction calculations.

Based on the Tax Rules Administration System architecture.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from app.models import BusinessProfile


# Multi-Year IRS Tax Rules (Historical and Projected)
# Source: IRS Revenue Procedures and Publication 505
DEFAULT_TAX_RULES = {
    2023: {
        'standard_deductions': {
            'single': 13850,
            'married_jointly': 27700,
            'married_separately': 13850,
            'head_of_household': 20800,
        },
        'tax_brackets': [
            {'rate': 10, 'limit': 11000},   # 10% on income up to $11,000
            {'rate': 12, 'limit': 44725},   # 12% on income $11,001 to $44,725
            {'rate': 22, 'limit': 95375},   # 22% on income $44,726 to $95,375
            {'rate': 24, 'limit': 182100},  # 24% on income $95,376 to $182,100
            {'rate': 32, 'limit': 231250},  # 32% on income $182,101 to $231,250
            {'rate': 35, 'limit': 578125},  # 35% on income $231,251 to $578,125
            {'rate': 37, 'limit': float('inf')},  # 37% on income over $578,125
        ],
        'self_employment_tax_rate': 0.153,  # 15.3% (Social Security + Medicare)
        'qbi_deduction_rate': 0.20,  # 20% Qualified Business Income deduction
        'ss_wage_base': 160200,  # Social Security wage base for 2023
    },
    2024: {
        'standard_deductions': {
            'single': 14600,
            'married_jointly': 29200,
            'married_separately': 14600,
            'head_of_household': 21900,
        },
        'tax_brackets': [
            {'rate': 10, 'limit': 11600},   # 10% on income up to $11,600
            {'rate': 12, 'limit': 47150},   # 12% on income $11,601 to $47,150
            {'rate': 22, 'limit': 100525},  # 22% on income $47,151 to $100,525
            {'rate': 24, 'limit': 191950},  # 24% on income $100,526 to $191,950
            {'rate': 32, 'limit': 243725},  # 32% on income $191,951 to $243,725
            {'rate': 35, 'limit': 609350},  # 35% on income $243,726 to $609,350
            {'rate': 37, 'limit': float('inf')},  # 37% on income over $609,350
        ],
        'self_employment_tax_rate': 0.153,  # 15.3% (Social Security + Medicare)
        'qbi_deduction_rate': 0.20,  # 20% Qualified Business Income deduction
        'ss_wage_base': 168600,  # Social Security wage base for 2024
    },
    2025: {
        'standard_deductions': {
            'single': 15000,
            'married_jointly': 30000,
            'married_separately': 15000,
            'head_of_household': 22500,
        },
        'tax_brackets': [
            {'rate': 10, 'limit': 11925},   # 10% on income up to $11,925
            {'rate': 12, 'limit': 48475},   # 12% on income $11,926 to $48,475
            {'rate': 22, 'limit': 103350},  # 22% on income $48,476 to $103,350
            {'rate': 24, 'limit': 197300},  # 24% on income $103,351 to $197,300
            {'rate': 32, 'limit': 250525},  # 32% on income $197,301 to $250,525
            {'rate': 35, 'limit': 626350},  # 35% on income $250,526 to $626,350
            {'rate': 37, 'limit': float('inf')},  # 37% on income over $626,350
        ],
        'self_employment_tax_rate': 0.153,  # 15.3% (Social Security + Medicare)
        'qbi_deduction_rate': 0.20,  # 20% Qualified Business Income deduction
        'ss_wage_base': 176100,  # Social Security wage base for 2025
    },
    2026: {
        'standard_deductions': {
            'single': 14600,
            'married_jointly': 29200,
            'married_separately': 14600,
            'head_of_household': 21900,
        },
        'tax_brackets': [
            {'rate': 10, 'limit': 11600},   # 10% on income up to $11,600
            {'rate': 12, 'limit': 47150},   # 12% on income $11,601 to $47,150
            {'rate': 22, 'limit': 100525},  # 22% on income $47,151 to $100,525
            {'rate': 24, 'limit': 191950},  # 24% on income $100,526 to $191,950
            {'rate': 32, 'limit': 243725},  # 32% on income $191,951 to $243,725
            {'rate': 35, 'limit': 609350},  # 35% on income $243,726 to $609,350
            {'rate': 37, 'limit': float('inf')},  # 37% on income over $609,350
        ],
        'self_employment_tax_rate': 0.153,  # 15.3% (Social Security + Medicare)
        'qbi_deduction_rate': 0.20,  # 20% Qualified Business Income deduction
        'ss_wage_base': 168600,  # Social Security wage base for 2026 (projected)
    }
}


class TaxCalculationEngine:
    """
    Professional tax calculation engine for business profiles

    Calculates:
    - Audit risk scores based on IRS red flags
    - Potential tax savings opportunities
    - Self-employment tax estimates
    - QBI deductions
    - Entity optimization recommendations
    """

    def __init__(self, tax_year: int = 2025):
        """
        Initialize tax engine with specific tax year rules

        Args:
            tax_year: Tax year to use for calculations (2023-2026)
                     Defaults to 2025 (current year)

        Raises:
            ValueError: If tax_year is not supported
        """
        if tax_year not in DEFAULT_TAX_RULES:
            available_years = sorted(DEFAULT_TAX_RULES.keys())
            raise ValueError(
                f"Tax year {tax_year} not supported. "
                f"Available years: {available_years}. "
                f"Using default year 2025."
            )

        self.tax_year = tax_year
        self.rules = DEFAULT_TAX_RULES[tax_year]

    def calculate_audit_risk(self, profile: BusinessProfile) -> Dict[str, Any]:
        """
        Calculate audit risk score based on IRS red flags

        IRS Red Flags:
        - High gross receipts (>$100k = audit rate increases)
        - High gross receipts (>$500k = significantly higher audit rate)
        - Payroll (employers have higher scrutiny)
        - Multi-state operations (nexus complexity)
        - Inventory management (COGS verification)
        - High deduction-to-income ratio
        - Consistent losses (hobby loss rules)
        - Cash-heavy businesses
        - Large charitable deductions
        - Home office deductions
        - Vehicle deductions

        Returns:
            dict: {
                'level': 'Low' | 'Medium' | 'High',
                'score': int (0-100),
                'percentage': int (0-100),
                'color': str (hex color),
                'risk_factors': list of identified risk factors,
                'recommendations': list of risk mitigation strategies
            }
        """
        risk_score = 0
        risk_factors = []
        recommendations = []

        # Revenue-based risk (IRS audit rates increase with revenue)
        revenue = profile.annual_revenue or 0
        if revenue > 500000:
            risk_score += 25
            risk_factors.append(f'High gross receipts (${revenue:,.0f} > $500k)')
            recommendations.append('Maintain detailed revenue documentation and reconciliation')
        elif revenue > 100000:
            risk_score += 15
            risk_factors.append(f'Moderate gross receipts (${revenue:,.0f} > $100k)')

        # Payroll complexity
        if profile.has_employees:
            risk_score += 20
            risk_factors.append(f'Payroll obligations ({profile.employee_count or "unknown"} employees)')
            recommendations.append('Ensure 941 quarterly filings are timely and accurate')
            recommendations.append('Verify W-2/W-3 accuracy before year-end filing')

        # Multi-state nexus complexity
        complexity_flags = (profile.data or {}).get('complexity_flags', [])
        operating_states = profile.operating_states or []

        if 'multiple_states' in complexity_flags or len(operating_states) > 1:
            risk_score += 30
            risk_factors.append('Multi-state operations (nexus complexity)')
            recommendations.append('Review state income tax filing requirements')
            recommendations.append('Ensure sales tax nexus compliance in all states')

        # Inventory management (COGS scrutiny)
        if 'inventory' in complexity_flags:
            risk_score += 15
            risk_factors.append('Inventory tracking (COGS verification required)')
            recommendations.append('Maintain physical inventory counts and valuation records')

        # Contractor payments (1099 compliance)
        if profile.contractor_count and profile.contractor_count > 0:
            risk_score += 10
            risk_factors.append(f'Contractor payments ({profile.contractor_count} contractors)')
            recommendations.append('Ensure all 1099-NEC forms issued by Jan 31')

        # Home office deduction (high scrutiny item)
        if profile.has_home_office:
            risk_score += 12
            risk_factors.append('Home office deduction claimed')
            recommendations.append('Maintain home office square footage documentation')
            recommendations.append('Ensure exclusive business use of home office space')

        # Vehicle deduction (high scrutiny item)
        if profile.has_vehicle or (profile.vehicle_deduction and profile.vehicle_deduction > 0):
            risk_score += 10
            risk_factors.append('Vehicle deduction claimed')
            recommendations.append('Maintain contemporaneous mileage logs')
            recommendations.append('Document business purpose for each trip')

        # Loss patterns (hobby loss rules)
        if profile.reported_losses and profile.reported_losses >= 3:
            risk_score += 20
            risk_factors.append(f'Consecutive losses reported ({profile.reported_losses} years)')
            recommendations.append('Document profit motive and business operation manner')

        # Cash business red flag
        if profile.high_cash_transactions:
            risk_score += 15
            risk_factors.append('High cash transaction volume')
            recommendations.append('Implement robust cash receipt documentation system')

        # Charitable contribution scrutiny
        if profile.large_charitable_contributions:
            risk_score += 8
            risk_factors.append('Large charitable contributions')
            recommendations.append('Obtain and retain written acknowledgments for donations >$250')

        # Deduction ratio analysis
        if revenue > 0:
            expense_ratio = profile.expense_ratio or 0
            if expense_ratio > 0.80:  # Expenses > 80% of revenue
                risk_score += 15
                risk_factors.append(f'High expense ratio ({expense_ratio*100:.0f}% of revenue)')
                recommendations.append('Ensure all deductions are ordinary and necessary')

        # Cap risk score at 100
        risk_score = min(risk_score, 100)

        # Determine risk level and color
        if risk_score < 30:
            level = 'Low'
            color = '#4CAF50'  # Green
            if not risk_factors:
                risk_factors.append('Standard business operations')
                recommendations.append('Continue maintaining good recordkeeping practices')
        elif risk_score < 60:
            level = 'Medium'
            color = '#FFA500'  # Orange
            recommendations.append('Consider engaging a tax professional for review')
        else:
            level = 'High'
            color = '#FF6B00'  # Orange-Red
            recommendations.append('STRONGLY RECOMMENDED: Engage a CPA for tax preparation')
            recommendations.append('Consider IRS audit protection insurance')

        return {
            'level': level,
            'score': risk_score,
            'percentage': risk_score,
            'color': color,
            'risk_factors': risk_factors,
            'recommendations': recommendations
        }

    def calculate_tax_savings(self, profile: BusinessProfile) -> Dict[str, Any]:
        """
        Calculate potential tax savings opportunities

        Considers:
        - Entity type optimization (LLC, S-Corp, C-Corp)
        - QBI deduction (20% pass-through deduction)
        - Self-employment tax optimization
        - Retirement plan contributions
        - Business expense optimization
        - Home office deduction
        - Vehicle deduction
        - Section 179 depreciation
        - Payroll tax optimization (S-Corp salary vs distribution)

        Returns:
            dict: {
                'amount': str (formatted currency),
                'percentage': int,
                'breakdown': dict of savings by category,
                'opportunities': list of specific recommendations,
                'entity_recommendation': str (optimal entity type)
            }
        """
        revenue = profile.annual_revenue or 0
        if revenue == 0:
            return {
                'amount': '$0',
                'percentage': 0,
                'breakdown': {},
                'opportunities': ['Start tracking revenue to identify tax savings opportunities'],
                'entity_recommendation': 'Sole Proprietor (current)'
            }

        savings_breakdown = {}
        opportunities = []
        total_savings = 0

        # Base deduction optimization (15% of revenue as benchmark)
        base_optimization = revenue * 0.15
        savings_breakdown['Base Deduction Optimization'] = base_optimization
        opportunities.append(f'Maximize ordinary and necessary business deductions')

        # QBI Deduction (20% of qualified business income for pass-through entities)
        if profile.business_type.value in ['sole_proprietor', 'llc', 's_corp']:
            # Simplified QBI calculation (actual has income phase-outs)
            estimated_qbi = revenue * 0.20  # Assume 20% of revenue qualifies
            qbi_tax_savings = estimated_qbi * 0.22  # Assuming 22% marginal rate
            savings_breakdown['QBI Pass-Through Deduction'] = qbi_tax_savings
            opportunities.append(f'Claim 20% QBI deduction (estimated ${qbi_tax_savings:,.0f} tax savings)')
            total_savings += qbi_tax_savings

        # Self-employment tax optimization (for sole props and LLCs)
        if profile.business_type.value in ['sole_proprietor', 'llc']:
            # S-Corp election could save ~50% of SE tax on reasonable portion
            if revenue > 60000:  # S-Corp makes sense above $60k revenue
                potential_se_savings = (revenue * 0.50) * self.rules['self_employment_tax_rate']
                savings_breakdown['S-Corp Election (SE Tax Reduction)'] = potential_se_savings
                opportunities.append(f'Consider S-Corp election to reduce self-employment tax')
                total_savings += potential_se_savings

        # Retirement plan contributions (Solo 401k, SEP IRA)
        if revenue > 50000:
            max_contribution = min(revenue * 0.20, 66000)  # 2026 Solo 401k limit
            retirement_tax_savings = max_contribution * 0.24  # Assuming 24% marginal rate
            savings_breakdown['Retirement Plan Contributions'] = retirement_tax_savings
            opportunities.append(f'Max out Solo 401(k) contributions (${max_contribution:,.0f})')
            total_savings += retirement_tax_savings

        # Payroll tax optimization (for employers)
        complexity_flags = (profile.data or {}).get('complexity_flags', [])
        if 'employees' in complexity_flags or profile.has_employees:
            payroll_savings = 5000  # Average savings from proper payroll tax planning
            savings_breakdown['Payroll Tax Optimization'] = payroll_savings
            opportunities.append('Review FICA withholding and employer tax credits')
            total_savings += payroll_savings

        # 1099 contractor optimization
        if 'contractors' in complexity_flags or (profile.contractor_count and profile.contractor_count > 0):
            contractor_savings = 2000  # Proper classification and deduction tracking
            savings_breakdown['Contractor Management'] = contractor_savings
            opportunities.append('Ensure proper contractor classification and expense tracking')
            total_savings += contractor_savings

        # Home office deduction (if not already claimed)
        if not profile.has_home_office and profile.business_type.value in ['sole_proprietor', 'llc']:
            home_office_savings = 1500  # Simplified method $5/sq ft, average 300 sq ft
            savings_breakdown['Home Office Deduction'] = home_office_savings
            opportunities.append('Claim home office deduction (simplified method)')
            total_savings += home_office_savings

        # Vehicle deduction (if applicable)
        if profile.has_vehicle or 'rideshare' in (profile.industry or '').lower():
            vehicle_savings = 3500  # Standard mileage deduction, avg 5000 miles @ $0.70/mile
            savings_breakdown['Vehicle/Mileage Deduction'] = vehicle_savings
            opportunities.append('Maintain mileage logs for vehicle deduction')
            total_savings += vehicle_savings

        # Equipment depreciation (Section 179)
        if profile.has_equipment_purchases:
            depreciation_savings = 2500  # Average Section 179 tax benefit
            savings_breakdown['Section 179 Depreciation'] = depreciation_savings
            opportunities.append('Leverage Section 179 for equipment purchases')
            total_savings += depreciation_savings

        # Health insurance deduction (self-employed)
        if profile.business_type.value in ['sole_proprietor', 'llc']:
            health_insurance_savings = 2000  # Average self-employed health insurance deduction
            savings_breakdown['Self-Employed Health Insurance'] = health_insurance_savings
            opportunities.append('Deduct self-employed health insurance premiums')
            total_savings += health_insurance_savings

        # Cap total savings at 30% of revenue (realistic ceiling)
        total_savings = min(total_savings + base_optimization, revenue * 0.30)

        # Entity optimization recommendation
        entity_recommendation = self._recommend_entity_type(profile, revenue)

        return {
            'amount': f'${total_savings:,.0f}',
            'percentage': int((total_savings / revenue * 100) if revenue > 0 else 15),
            'breakdown': {k: f'${v:,.0f}' for k, v in savings_breakdown.items()},
            'opportunities': opportunities,
            'entity_recommendation': entity_recommendation
        }

    def _recommend_entity_type(self, profile: BusinessProfile, revenue: float) -> str:
        """
        Recommend optimal entity type based on revenue and complexity

        Rules:
        - < $40k revenue: Sole Proprietor (simplicity)
        - $40k-$60k: LLC (liability protection)
        - $60k-$200k: S-Corp (SE tax savings)
        - > $200k with growth: C-Corp (lower corporate rate, retain earnings)
        """
        current_entity = profile.business_type.value.replace('_', ' ').title()

        if revenue < 40000:
            return f'{current_entity} (Sole Proprietor recommended for simplicity)'
        elif revenue < 60000:
            if profile.business_type.value == 'sole_proprietor':
                return 'LLC (upgrade for liability protection)'
            return f'{current_entity} (current structure appropriate)'
        elif revenue < 200000:
            if profile.business_type.value in ['sole_proprietor', 'llc']:
                return 'S-Corp (election recommended for SE tax savings)'
            return f'{current_entity} (current structure appropriate)'
        else:
            # High revenue - evaluate C-Corp for tax deferral and growth
            if profile.business_type.value in ['sole_proprietor', 'llc']:
                return 'S-Corp or C-Corp (consult CPA for optimal structure)'
            elif profile.business_type.value == 's_corp':
                return 'S-Corp or consider C-Corp for retained earnings (consult CPA)'
            return f'{current_entity} (current structure appropriate)'

    def calculate_self_employment_tax(self, net_profit: float) -> Dict[str, float]:
        """
        Calculate self-employment tax (Social Security + Medicare)

        Uses the correct Social Security wage base for the tax year.

        Args:
            net_profit: Net business profit (Schedule C profit)

        Returns:
            dict: {
                'social_security': float,
                'medicare': float,
                'total_se_tax': float,
                'deductible_portion': float (50% of SE tax),
                'ss_wage_base': float (for reference),
                'tax_year': int (year used for calculation)
            }
        """
        # Get SS wage base for this tax year
        ss_wage_base = self.rules.get('ss_wage_base', 168600)

        # SE tax is calculated on 92.35% of net profit
        se_income = net_profit * 0.9235

        # Social Security: 12.4% on income up to wage base
        social_security = min(se_income, ss_wage_base) * 0.124

        # Medicare: 2.9% on all income
        medicare = se_income * 0.029

        # Additional Medicare tax: 0.9% on income over threshold ($200k for single)
        if se_income > 200000:
            medicare += (se_income - 200000) * 0.009

        total_se_tax = social_security + medicare
        deductible_portion = total_se_tax * 0.50  # 50% deductible

        return {
            'social_security': social_security,
            'medicare': medicare,
            'total_se_tax': total_se_tax,
            'deductible_portion': deductible_portion,
            'ss_wage_base': ss_wage_base,
            'tax_year': self.tax_year
        }

    def estimate_quarterly_tax_payments(self, profile: BusinessProfile) -> Dict[str, Any]:
        """
        Estimate quarterly estimated tax payments (Form 1040-ES)

        Args:
            profile: BusinessProfile instance

        Returns:
            dict: {
                'quarterly_amount': float,
                'annual_total': float,
                'due_dates': list of due dates,
                'breakdown': dict of tax components
            }
        """
        revenue = profile.annual_revenue or 0

        # Assume 30% profit margin (conservative)
        estimated_profit = revenue * 0.30

        # Calculate SE tax
        se_tax = self.calculate_self_employment_tax(estimated_profit)

        # Calculate income tax (simplified - assume 22% effective rate)
        income_tax = estimated_profit * 0.22

        # Total annual tax
        annual_total = se_tax['total_se_tax'] + income_tax

        # Quarterly payment
        quarterly_amount = annual_total / 4

        # 2026 due dates (15th of 4th, 6th, 9th month, and 1st month of next year)
        due_dates = [
            'April 15, 2026',
            'June 15, 2026',
            'September 15, 2026',
            'January 15, 2027'
        ]

        return {
            'quarterly_amount': quarterly_amount,
            'annual_total': annual_total,
            'due_dates': due_dates,
            'breakdown': {
                'self_employment_tax': se_tax['total_se_tax'],
                'income_tax': income_tax
            }
        }


# Singleton instance for easy import (defaults to current year 2025)
tax_engine = TaxCalculationEngine(tax_year=2025)


# Convenience functions for direct use (use current year by default)
def calculate_audit_risk(profile: BusinessProfile, tax_year: int = 2025) -> Dict[str, Any]:
    """
    Calculate audit risk score for a business profile

    Args:
        profile: BusinessProfile instance
        tax_year: Tax year to use for calculations (2023-2026), defaults to 2025

    Returns:
        dict: Audit risk assessment with score, level, and recommendations
    """
    engine = TaxCalculationEngine(tax_year=tax_year)
    return engine.calculate_audit_risk(profile)


def calculate_tax_savings(profile: BusinessProfile, tax_year: int = 2025) -> Dict[str, Any]:
    """
    Calculate potential tax savings for a business profile

    Args:
        profile: BusinessProfile instance
        tax_year: Tax year to use for calculations (2023-2026), defaults to 2025

    Returns:
        dict: Tax savings opportunities with amount, percentage, and breakdown
    """
    engine = TaxCalculationEngine(tax_year=tax_year)
    return engine.calculate_tax_savings(profile)


def calculate_self_employment_tax(net_profit: float, tax_year: int = 2025) -> Dict[str, float]:
    """
    Calculate self-employment tax

    Args:
        net_profit: Net business profit
        tax_year: Tax year to use for calculations (2023-2026), defaults to 2025

    Returns:
        dict: SE tax breakdown with social security, medicare, and total
    """
    engine = TaxCalculationEngine(tax_year=tax_year)
    return engine.calculate_self_employment_tax(net_profit)


def estimate_quarterly_payments(profile: BusinessProfile, tax_year: int = 2025) -> Dict[str, Any]:
    """
    Estimate quarterly tax payments

    Args:
        profile: BusinessProfile instance
        tax_year: Tax year to use for calculations (2023-2026), defaults to 2025

    Returns:
        dict: Quarterly payment estimates with due dates
    """
    engine = TaxCalculationEngine(tax_year=tax_year)
    return engine.estimate_quarterly_tax_payments(profile)
