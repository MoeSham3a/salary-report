"""
Salary Calculation Engine — جدول رواتب و أجور
All Excel formulas replicated in Python.
"""
import math
from datetime import date

# ---------------------------------------------------------------------------
# Minimum Wage Schedule (Lebanese labor law)
# List of (start_date, end_date, minimum_monthly_salary)
# Ordered newest-first for quick lookup.
# ---------------------------------------------------------------------------
MINIMUM_WAGES = [
    (date(2025, 8, 1),  None,              28_000_000),
    (date(2024, 4, 1),  date(2025, 7, 31), 18_000_000),
    (date(2023, 5, 1),  date(2024, 3, 31),  9_000_000),
    (date(2023, 4, 1),  date(2023, 4, 30),  3_667_000),
    (date(2022, 10, 1), date(2023, 3, 31),  2_600_000),
    (date(2022, 4, 1),  date(2022, 9, 30),  2_000_000),
    (date(2022, 1, 1),  date(2022, 3, 31),  1_100_000),
    (date(2012, 2, 1),  date(2021, 12, 31),   675_000),
]

# Quarter end-dates: Q1=Mar 31, Q2=Jun 30, Q3=Sep 30, Q4=Dec 31
_QUARTER_END = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}


def get_minimum_wage(quarter, year):
    """Return the minimum monthly salary for the given quarter/year."""
    month, day = _QUARTER_END.get(quarter, (12, 31))
    ref = date(year, month, day)
    for start, end, amount in MINIMUM_WAGES:
        if end is None:
            if ref >= start:
                return amount
        elif start <= ref <= end:
            return amount
    return 0  # Before 2012


# ---------------------------------------------------------------------------
# Family Allowance Cap Schedule (max yearly eligible for 6%)
# ---------------------------------------------------------------------------
FAMILY_ALLOWANCE_CAPS = [
    (date(2025, 7, 1),  None,              216_000_000),
    (date(2024, 1, 1),  date(2025, 6, 30), 144_000_000),
    (date(2022, 10, 1), date(2023, 12, 31), 41_100_000),
    (date(2022, 4, 1),  date(2022, 9, 30),  33_900_000),
    (date(2019, 1, 1),  date(2022, 3, 31),  18_000_000),
]


def get_family_allowance_cap(quarter, year):
    """Return the max yearly amount eligible for 6% family allowance."""
    month, day = _QUARTER_END.get(quarter, (12, 31))
    ref = date(year, month, day)
    for start, end, amount in FAMILY_ALLOWANCE_CAPS:
        if end is None:
            if ref >= start:
                return amount
        elif start <= ref <= end:
            return amount
    return 18_000_000  # Default fallback


# ---------------------------------------------------------------------------
# Sickness & Maternity Cap Schedule (max yearly eligible for 11%)
# ---------------------------------------------------------------------------
SICKNESS_MATERNITY_CAPS = [
    (date(2025, 8, 1),  None,              1_440_000_000),
    (date(2024, 4, 1),  date(2025, 7, 31), 1_080_000_000),
    (date(2024, 3, 1),  date(2024, 3, 31),   540_000_000),
    (date(2023, 9, 1),  date(2024, 2, 29),   216_000_000),
    (date(2022, 10, 1), date(2023, 8, 31),    67_200_000),
    (date(2022, 7, 1),  date(2022, 9, 30),    60_000_000),
    (date(2022, 4, 1),  date(2022, 6, 30),    45_900_000),
    (date(2019, 1, 1),  date(2022, 3, 31),    30_000_000),
]


def get_sickness_maternity_cap(quarter, year):
    """Return the max yearly amount eligible for 11% sickness & maternity."""
    month, day = _QUARTER_END.get(quarter, (12, 31))
    ref = date(year, month, day)
    for start, end, amount in SICKNESS_MATERNITY_CAPS:
        if end is None:
            if ref >= start:
                return amount
        elif start <= ref <= end:
            return amount
    return 30_000_000  # Default fallback


# ---------------------------------------------------------------------------
# Family Payment Brackets (monthly wife/child allowance amounts)
# ---------------------------------------------------------------------------
FAMILY_PAYMENT_BRACKETS = [
    (date(2025, 7, 1),  None,               1_200_000, 660_000),  # wife, child per month
    (date(2024, 1, 1),  date(2025, 6, 30),    600_000, 330_000),
    (date(2012, 1, 1),  date(2023, 12, 31),    60_000,  33_000),
]


def get_family_payments(quarter, year):
    """Return (wife_quarterly, child_quarterly) payment amounts."""
    month, day = _QUARTER_END.get(quarter, (12, 31))
    ref = date(year, month, day)
    for start, end, wife_monthly, child_monthly in FAMILY_PAYMENT_BRACKETS:
        if end is None:
            if ref >= start:
                return wife_monthly * 3, child_monthly * 3
        elif start <= ref <= end:
            return wife_monthly * 3, child_monthly * 3
    return 60_000 * 3, 33_000 * 3  # Default fallback


# ---------------------------------------------------------------------------
# Transport Allowance Brackets (per working day)
# ---------------------------------------------------------------------------
TRANSPORT_BRACKETS = [
    (date(2024, 2, 15), None,              450_000),
    (date(2023, 4, 26), date(2024, 2, 14), 250_000),
    (date(2022, 8, 18), date(2023, 4, 25),  95_000),
    (date(2022, 2, 3),  date(2022, 8, 17),  65_000),
    (date(2021, 10, 1), date(2022, 2, 2),   24_000),
    (date(2012, 1, 1),  date(2021, 9, 30),   8_000),
]


def get_transport_per_day(quarter, year):
    """Return the transport allowance per working day."""
    month, day = _QUARTER_END.get(quarter, (12, 31))
    ref = date(year, month, day)
    for start, end, amount in TRANSPORT_BRACKETS:
        if end is None:
            if ref >= start:
                return amount
        elif start <= ref <= end:
            return amount
    return 8_000  # Default fallback


# ---------------------------------------------------------------------------
# Other Constants
# ---------------------------------------------------------------------------
WORK_DAYS_PER_MONTH = 26
MONTHS_PER_QUARTER = 3

# ---------------------------------------------------------------------------
# Family Deduction Brackets (yearly amounts for tax deduction)
# (employee_yearly, wife_yearly, child_yearly)
# ---------------------------------------------------------------------------
FAMILY_DEDUCTION_BRACKETS = [
    (date(2025, 1, 1), None,              450_000_000, 225_000_000, 45_000_000),
    (date(2024, 1, 1), date(2024, 12, 31), 398_437_500, 198_437_500, 39_687_500),
    (date(2022, 1, 1), date(2023, 12, 31),  37_500_000,  12_500_000,  2_500_000),
    (date(2012, 1, 1), date(2021, 12, 31),   7_500_000,   2_500_000,    500_000),
]

MAX_CHILDREN_DEDUCTION = 5


def get_family_deductions(quarter, year):
    """Return (employee_yearly, wife_yearly, child_yearly) deduction amounts."""
    month, day = _QUARTER_END.get(quarter, (12, 31))
    ref = date(year, month, day)
    for start, end, emp_y, wife_y, child_y in FAMILY_DEDUCTION_BRACKETS:
        if end is None:
            if ref >= start:
                return emp_y, wife_y, child_y
        elif start <= ref <= end:
            return emp_y, wife_y, child_y
    return 7_500_000, 2_500_000, 500_000  # Default fallback


PERSONAL_DEDUCTION_F = 1_250_000  # Foreign 'F' — kept separate

TAX_RATE = 0.02

END_OF_SERVICE_RATE = 8.5 / 100
FAMILY_ALLOWANCE_RATE = 6.0 / 100
SICKNESS_MATERNITY_RATE = 11.0 / 100

COMBINED_CONTRIBUTION_RATE = 25.5 / 100


def calculate_employee_quarterly(emp, quarter=1, year=2026):
    """
    Calculate all quarterly fields for one employee dict.
    Input keys: name, monthly_salary, is_foreign, is_married, num_children
    quarter/year used for dynamic family allowance cap lookup.
    Returns dict with all calculated fields.
    """
    salary = emp.get('monthly_salary', 0) or 0
    foreign = str(emp.get('is_foreign', 'no')).upper()
    married_input = str(emp.get('is_married', 'no')).lower()
    children_input = emp.get('num_children', 0) or 0

    # Foreign override
    children = 0 if foreign == 'YES' else children_input
    married = '' if foreign == 'YES' else married_input

    # Total quarterly salary
    total_salary = salary * MONTHS_PER_QUARTER

    # Social security
    end_of_service = total_salary * END_OF_SERVICE_RATE

    family_cap_yearly = get_family_allowance_cap(quarter, year)
    quarterly_family_cap = family_cap_yearly / 4
    family_6 = min(total_salary * FAMILY_ALLOWANCE_RATE,
                   quarterly_family_cap * FAMILY_ALLOWANCE_RATE)

    sickness_cap_yearly = get_sickness_maternity_cap(quarter, year)
    quarterly_sickness_cap = sickness_cap_yearly / 4
    sickness_11 = min(total_salary * SICKNESS_MATERNITY_RATE,
                      quarterly_sickness_cap * SICKNESS_MATERNITY_RATE)

    total_contributions = end_of_service + family_6 + sickness_11

    # Family allowance payments
    marriage_quarterly, child_quarterly = get_family_payments(quarter, year)
    child_allowance = children * child_quarterly
    marriage_allowance = marriage_quarterly if married == 'yes' else 0
    family_paid = child_allowance + marriage_allowance

    # Amount due
    amount_due = total_contributions - family_paid

    # Tax deductions
    emp_yearly, wife_yearly, child_yearly = get_family_deductions(quarter, year)
    capped_children = min(children, MAX_CHILDREN_DEDUCTION)
    child_deduction = capped_children * (child_yearly / 4)
    marriage_deduction = (wife_yearly / 4) if married == 'yes' else 0

    if foreign in ('YES', 'NO'):
        personal_deduction = emp_yearly / 4
    elif foreign == 'F':
        personal_deduction = PERSONAL_DEDUCTION_F
    else:
        personal_deduction = 0

    family_deduction = child_deduction + marriage_deduction + personal_deduction

    # Taxable amount
    taxable = max(total_salary - family_deduction, 0)

    # Tax
    tax = taxable * TAX_RATE

    # Transport
    has_name = bool(emp.get('name') and str(emp['name']).strip())
    transport_daily = get_transport_per_day(quarter, year)
    transport = (transport_daily * WORK_DAYS_PER_MONTH * MONTHS_PER_QUARTER) if has_name else 0

    return {
        'children_effective': children,
        'married_effective': married,
        'total_salary': total_salary,
        'end_of_service': end_of_service,
        'family_6': family_6,
        'sickness_11': sickness_11,
        'total_contributions': total_contributions,
        'family_paid': family_paid,
        'amount_due': amount_due,
        'family_deduction': family_deduction,
        'taxable': taxable,
        'tax': tax,
        'transport': transport,
    }


def calculate_employee_yearly(emp):
    """Calculate all yearly fields for one employee dict."""
    salary = emp.get('monthly_salary', 0) or 0
    foreign = str(emp.get('is_foreign', 'no')).upper()
    married_input = str(emp.get('is_married', 'no')).lower()
    children_input = emp.get('num_children', 0) or 0

    children = 0 if foreign == 'YES' else children_input
    married = '' if foreign == 'YES' else married_input

    total_salary = salary * 12

    contributions_25 = total_salary * COMBINED_CONTRIBUTION_RATE

    # Use Q4 of the year for yearly lookup
    marriage_quarterly, child_quarterly = get_family_payments(4, 0)  # fallback
    # For yearly, sum all 4 quarters (simplified: use same rate)
    child_allowance = children * child_quarterly * 4
    marriage_allowance = (marriage_quarterly * 4) if married == 'yes' else 0
    family_paid = child_allowance + marriage_allowance

    amount_due = contributions_25 - family_paid

    emp_yearly, wife_yearly, child_yearly = get_family_deductions(4, 0)  # fallback
    capped_children = min(children, MAX_CHILDREN_DEDUCTION)
    child_deduction = capped_children * child_yearly
    marriage_deduction = wife_yearly if married == 'yes' else 0

    if foreign in ('YES', 'NO'):
        personal_deduction = emp_yearly
    elif foreign == 'F':
        personal_deduction = PERSONAL_DEDUCTION_F * 4
    else:
        personal_deduction = 0

    family_deduction = child_deduction + marriage_deduction + personal_deduction
    taxable = max(total_salary - family_deduction, 0)
    tax = taxable * TAX_RATE

    has_name = bool(emp.get('name') and str(emp['name']).strip())
    transport = (get_transport_per_day(4, 0) * WORK_DAYS_PER_MONTH * 12) if has_name else 0

    return {
        'children_effective': children,
        'married_effective': married,
        'total_salary': total_salary,
        'contributions_25': contributions_25,
        'family_paid': family_paid,
        'amount_due': amount_due,
        'family_deduction': family_deduction,
        'taxable': taxable,
        'tax': tax,
        'transport': transport,
    }


def calculate_summary(employees, report_type='quarter', quarter=1, year=2026):
    """
    Calculate the summary table from a list of employee dicts (already calculated).
    report_type: 'quarter' or 'year'
    """
    if report_type == 'quarter':
        results = [calculate_employee_quarterly(emp, quarter, year) for emp in employees]
    else:
        results = [calculate_employee_yearly(emp) for emp in employees]

    total_salaries = sum(r['total_salary'] for r in results)
    total_family_paid = sum(r['family_paid'] for r in results)
    total_transport = sum(r['transport'] for r in results)
    total_deductions = sum(r['family_deduction'] for r in results)
    total_taxable = sum(r['taxable'] for r in results)
    total_tax = sum(r['tax'] for r in results)

    benefits = total_family_paid + total_transport
    total_paid = total_salaries + benefits
    transport_deduct = -total_transport
    family_deduct = -total_family_paid
    net_salaries = total_paid + family_deduct + transport_deduct
    tax_due = math.ceil(total_tax / 1000) * 1000

    return {
        'مجموع الرواتب': total_salaries,
        'المنافع النقدية والعينية': benefits,
        'مجموع المبالغ المدفوعة': total_paid,
        'تعويضات نقل وانتقال': transport_deduct,
        'التعويضات العائلية': family_deduct,
        'مجموع الرواتب_net': net_salaries,
        'التنزيل العائلي': total_deductions,
        'المبلغ الخاضع': total_taxable,
        'الضريبة المتوجبة': tax_due,
    }
