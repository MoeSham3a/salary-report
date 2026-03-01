"""
جدول رواتب و أجور - Salary & Wages Calculator
===============================================
Replicates all Excel formulas in Python/pandas.

Usage:
    python salary_data.py                        # Print full calculated tables
    python -i salary_data.py                     # Interactive mode
    
Interactive examples:
    df["اسم الأجير"]                             # List employee names
    df[df["الراتب الشهري"] > 0]                  # Employees with salary
    df["الراتب الشهري"].sum()                     # Total monthly salaries
    add_employee("أحمد", 10000000, married="yes", children=2)  # Add employee
    recalculate()                                 # Recalculate all
"""
import sys
import io

def _setup_encoding():
    """Fix Windows console encoding for Arabic output."""
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except Exception:
            pass

import pandas as pd
import numpy as np
import glob
import os

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 500)
pd.set_option('display.max_colwidth', 40)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = r"C:\Users\mo7am\AppData\Local\Python\bin\python.exe"

# ---------------------------------------------------------------------------
# Constants (from Excel cells P28, P29, P30)
# ---------------------------------------------------------------------------
TRANSPORT_PER_DAY = 450_000            # بدل نقل per work day
WORK_DAYS_PER_MONTH = 26               # working days per month
MONTHS_PER_QUARTER = 3                 # quarterly sheet

MAX_SICKNESS_MATERNITY_YEARLY = 1_680_000_000   # الكسب الأقصى لفرع المرض و الأمومة بالسنة
MAX_FAMILY_ALLOWANCES_YEARLY = 216_000_000       # الكسب الأقصى لفرع التعويضات العائلية بالسنة

# Per-quarter child/marriage allowance payments
CHILD_ALLOWANCE_QUARTERLY = 1_980_000      # per child per quarter (from N6: R6*1980000)
MARRIAGE_ALLOWANCE_QUARTERLY = 3_600_000   # if married (from O6)

# Tax deduction amounts (quarterly)
CHILD_DEDUCTION = 11_250_000           # per child (from E6: R6*11250000)
MARRIAGE_DEDUCTION = 56_250_000        # if married (from F6)
PERSONAL_DEDUCTION_RESIDENT = 112_500_000  # if not foreign (from G6)
PERSONAL_DEDUCTION_F = 1_250_000       # if foreign="F" (partial)

TAX_RATE = 0.02                        # 2% tax (from B6: C6*0.02)

# Social security rates
END_OF_SERVICE_RATE = 8.5 / 100        # نهاية الخدمة
FAMILY_ALLOWANCE_RATE = 6.0 / 100      # تعويضات عائلية
SICKNESS_MATERNITY_RATE = 11.0 / 100   # المرض و الأمومة

# Yearly constants (different from quarterly)
CHILD_ALLOWANCE_YEARLY = CHILD_ALLOWANCE_QUARTERLY * 4     # NOT USED - yearly sheet is simpler
COMBINED_CONTRIBUTION_RATE = 25.5 / 100  # yearly sheet uses single rate


# ---------------------------------------------------------------------------
# Load input data from Excel
# ---------------------------------------------------------------------------
def _find_excel():
    """Find the Excel file in the script directory."""
    files = glob.glob(os.path.join(SCRIPT_DIR, '*.xlsx'))
    xlsx_files = [f for f in files if not os.path.basename(f).startswith('~')]
    return xlsx_files[0] if xlsx_files else None

FILEPATH = _find_excel()


def load_inputs():
    """
    Read only the INPUT columns from the Excel monthly sheet.
    Input columns (user-entered): V=name, U=start date, Q=salary, R=children, S=married, T=foreign
    All other columns are calculated.
    """
    if FILEPATH is None:
        return pd.DataFrame()
    
    raw = pd.read_excel(FILEPATH, sheet_name=0, header=None)
    
    # Data rows are 5–23 (0-indexed), row 4 is headers, row 24 is TOTAL
    # Columns: V=21=name, U=20=start_date, Q=16=salary, T=19=foreign
    # R=17 and S=18 are actually formulas that depend on T, so we read the 
    # original input which is in R (children) and S (married) but only before
    # the IF(foreign) override.
    # In the Excel, R and S cells contain =IF(T="YES",0,) which means the actual
    # input for children/married is NOT in the formula sheet - it's typed by user.
    # Since the formula zeros them out for foreigners, we'll read from the 
    # data_only version and handle the foreign logic ourselves.
    
    # Read with data_only to get computed values
    data_start = 5  # row index (0-based)
    data_end = 23   # row index (0-based), inclusive
    
    rows = []
    for r in range(data_start, data_end + 1):
        row_num = raw.iloc[r, 22]  # W column = row number
        if pd.isna(row_num):
            continue
        
        name = raw.iloc[r, 21]           # V = اسم الأجير
        start_date = raw.iloc[r, 20]     # U = تاريخ بدء العمل
        salary = raw.iloc[r, 16]         # Q = الراتب الشهري
        foreign = raw.iloc[r, 19]        # T = اجنبي
        
        # For children and married, we need the RAW input (not formula result).
        # Since the formulas override to 0 for foreigners, we read the values
        # and treat non-foreign values as the real inputs.
        children = raw.iloc[r, 17]       # R = عدد الأولاد
        married = raw.iloc[r, 18]        # S = متزوج
        
        rows.append({
            'رقم': int(row_num),
            'اسم الأجير': name if pd.notna(name) else None,
            'تاريخ بدء العمل': start_date if pd.notna(start_date) else None,
            'الراتب الشهري': pd.to_numeric(salary, errors='coerce') or 0,
            'اجنبي': str(foreign).strip().upper() if pd.notna(foreign) else '',
            'عدد الأولاد_input': pd.to_numeric(children, errors='coerce') or 0,
            'متزوج_input': str(married).strip().lower() if pd.notna(married) else '',
        })
    
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Formula calculations — Monthly/Quarterly (شهري)
# ---------------------------------------------------------------------------
def calculate_quarterly(inputs_df):
    """
    Apply all Excel formulas to produce the full quarterly payroll table.
    Replicates the exact logic from the شهري sheet.
    """
    df = inputs_df.copy()
    
    # --- Step 1: Handle foreign override (Excel R6, S6) ---
    # =IF(T6="YES",0,)  — if foreign=YES, children=0 and married=0
    df['عدد الأولاد'] = df.apply(
        lambda r: 0 if r['اجنبي'] == 'YES' else r['عدد الأولاد_input'], axis=1
    )
    df['متزوج'] = df.apply(
        lambda r: '' if r['اجنبي'] == 'YES' else r['متزوج_input'], axis=1
    )
    
    # --- Step 2: Total quarterly salary (Excel P6: =Q6*3) ---
    df['مجموع الرواتب'] = df['الراتب الشهري'] * MONTHS_PER_QUARTER
    
    # --- Step 3: Social security contributions ---
    # End of service 8.5% (Excel J6: =P6*8.5/100)
    df['نهاية الخدمة 8.5%'] = df['مجموع الرواتب'] * END_OF_SERVICE_RATE
    
    # Family allowances 6% with cap (Excel K6: =MIN(P6*6/100,$P$30/4*6/100))
    quarterly_family_cap = MAX_FAMILY_ALLOWANCES_YEARLY / 4
    df['تعويضات عائلية 6%'] = np.minimum(
        df['مجموع الرواتب'] * FAMILY_ALLOWANCE_RATE,
        quarterly_family_cap * FAMILY_ALLOWANCE_RATE
    )
    
    # Sickness & maternity 11% with cap (Excel L6: =MIN(P6*11/100,$P$29/4*11/100))
    quarterly_sickness_cap = MAX_SICKNESS_MATERNITY_YEARLY / 4
    df['المرض و الامومة 11%'] = np.minimum(
        df['مجموع الرواتب'] * SICKNESS_MATERNITY_RATE,
        quarterly_sickness_cap * SICKNESS_MATERNITY_RATE
    )
    
    # Total contributions (Excel I6: =J6+K6+L6)
    df['مجموع الاشتراكات'] = (
        df['نهاية الخدمة 8.5%'] + 
        df['تعويضات عائلية 6%'] + 
        df['المرض و الامومة 11%']
    )
    
    # --- Step 4: Family allowance payments ---
    # Child allowance (Excel N6: =R6*1980000)
    df['_بدل_أولاد'] = df['عدد الأولاد'] * CHILD_ALLOWANCE_QUARTERLY
    
    # Marriage allowance (Excel O6: =IF(S6="yes",3600000,0))
    df['_بدل_زواج'] = df['متزوج'].apply(
        lambda v: MARRIAGE_ALLOWANCE_QUARTERLY if str(v).lower() == 'yes' else 0
    )
    
    # Total family allowances paid (Excel M6: =N6+O6)
    df['التعويضات العائلية المدفوعة'] = df['_بدل_أولاد'] + df['_بدل_زواج']
    
    # --- Step 5: Amount due (Excel H6: =I6-M6) ---
    df['الفرق المستحق'] = df['مجموع الاشتراكات'] - df['التعويضات العائلية المدفوعة']
    
    # --- Step 6: Tax deductions ---
    # Children deduction (Excel E6: =R6*11250000)
    df['_تنزيل_أولاد'] = df['عدد الأولاد'] * CHILD_DEDUCTION
    
    # Marriage deduction (Excel F6: =IF(S6="yes",56250000,IF(S6="no",0,0)))
    df['_تنزيل_زواج'] = df['متزوج'].apply(
        lambda v: MARRIAGE_DEDUCTION if str(v).lower() == 'yes' else 0
    )
    
    # Personal deduction (Excel G6: =IF(T6="yes",112500000,IF(T6="no",112500000,IF(T6="F",1250000,0))))
    # NOTE: both "yes" (foreign) and "no" (not foreign) get 112,500,000!
    # Only "F" gets a reduced 1,250,000 and anything else gets 0
    def personal_deduction(foreign_val):
        f = str(foreign_val).upper()
        if f in ('YES', 'NO'):
            return PERSONAL_DEDUCTION_RESIDENT
        elif f == 'F':
            return PERSONAL_DEDUCTION_F
        else:
            return 0
    
    df['_تنزيل_شخصي'] = df['اجنبي'].apply(personal_deduction)
    
    # Total family deduction (Excel D6: =E6+F6+G6)
    df['التنزيل العائلي'] = df['_تنزيل_أولاد'] + df['_تنزيل_زواج'] + df['_تنزيل_شخصي']
    
    # --- Step 7: Taxable amount (Excel C6: =IF((P6-D6)<0,0,(P6-D6))) ---
    df['المبلغ الخاضع'] = np.maximum(df['مجموع الرواتب'] - df['التنزيل العائلي'], 0)
    
    # --- Step 8: Tax (Excel B6: =C6*0.02) ---
    df['الضريبة'] = df['المبلغ الخاضع'] * TAX_RATE
    
    # --- Step 9: Transport allowance (Excel A6: =IF(V6="",0,$P$28*26*3)) ---
    transport_quarterly = TRANSPORT_PER_DAY * WORK_DAYS_PER_MONTH * MONTHS_PER_QUARTER
    df['بدل نقل'] = df['اسم الأجير'].apply(
        lambda name: transport_quarterly if pd.notna(name) and str(name).strip() != '' else 0
    )
    
    # --- Clean up: drop internal columns, reorder ---
    display_cols = [
        'رقم',
        'اسم الأجير',
        'تاريخ بدء العمل',
        'اجنبي',
        'متزوج',
        'عدد الأولاد',
        'الراتب الشهري',
        'مجموع الرواتب',
        'نهاية الخدمة 8.5%',
        'تعويضات عائلية 6%',
        'المرض و الامومة 11%',
        'مجموع الاشتراكات',
        'التعويضات العائلية المدفوعة',
        'الفرق المستحق',
        'التنزيل العائلي',
        'المبلغ الخاضع',
        'الضريبة',
        'بدل نقل',
    ]
    
    result = df[display_cols].copy()
    return result


def calculate_summary(df):
    """
    Calculate summary rows (Excel rows 25, 28-36).
    Returns a dict with summary values.
    """
    total_salaries = df['مجموع الرواتب'].sum()
    total_family_paid = df['التعويضات العائلية المدفوعة'].sum()
    total_transport = df['بدل نقل'].sum()
    total_deductions = df['التنزيل العائلي'].sum()
    total_taxable = df['المبلغ الخاضع'].sum()
    total_tax = df['الضريبة'].sum()
    
    # مجموع الرواتب (F28: =P25)
    sum_salaries = total_salaries
    # المنافع النقدية والعينية (F29: =M25+A25) 
    benefits = total_family_paid + total_transport
    # مجموع المبالغ المدفوعة (F30: =SUM(F28:F29))
    total_paid = sum_salaries + benefits
    # تعويضات نقل وانتقال (F31: =-A25)
    transport_deduct = -total_transport
    # التعويضات العائلية (F32: =-M25)
    family_deduct = -total_family_paid
    # مجموع الرواتب net (F33: =F30+F32+F31)
    net_salaries = total_paid + family_deduct + transport_deduct
    # التنزيل العائلي (F34: =D25)
    family_deduction_total = total_deductions
    # المبلغ الخاضع (F35: =C25)
    taxable_total = total_taxable
    # الضريبة المتوجبة (F36: =ROUNDUP(B25,-3))
    tax_due = int(np.ceil(total_tax / 1000)) * 1000  # ROUNDUP to nearest 1000
    
    return {
        'مجموع الرواتب': sum_salaries,
        'المنافع النقدية والعينية': benefits,
        'مجموع المبالغ المدفوعة': total_paid,
        'تعويضات نقل وانتقال': transport_deduct,
        'التعويضات العائلية': family_deduct,
        'صافي الرواتب': net_salaries,
        'التنزيل العائلي': family_deduction_total,
        'المبلغ الخاضع': taxable_total,
        'الضريبة المتوجبة': tax_due,
    }


# ---------------------------------------------------------------------------
# Formula calculations — Yearly (سنوي)
# ---------------------------------------------------------------------------
def calculate_yearly(inputs_df):
    """
    Apply yearly sheet formulas.
    The yearly sheet is simpler — uses a combined 25.5% contribution rate.
    """
    df = inputs_df.copy()
    
    # Foreign override
    df['عدد الأولاد'] = df.apply(
        lambda r: 0 if r['اجنبي'] == 'YES' else r['عدد الأولاد_input'], axis=1
    )
    df['متزوج'] = df.apply(
        lambda r: '' if r['اجنبي'] == 'YES' else r['متزوج_input'], axis=1
    )
    
    # Yearly total = monthly * 12
    df['مجموع الرواتب'] = df['الراتب الشهري'] * 12
    
    # Combined contributions at 25.5%
    df['الإشتراكات 25.5%'] = df['مجموع الرواتب'] * COMBINED_CONTRIBUTION_RATE
    
    # Family allowances paid (yearly)
    child_allowance_yearly = CHILD_ALLOWANCE_QUARTERLY * 4
    marriage_allowance_yearly = MARRIAGE_ALLOWANCE_QUARTERLY * 4
    
    df['_بدل_أولاد'] = df['عدد الأولاد'] * child_allowance_yearly
    df['_بدل_زواج'] = df['متزوج'].apply(
        lambda v: marriage_allowance_yearly if str(v).lower() == 'yes' else 0
    )
    df['التعويضات العائلية المدفوعة'] = df['_بدل_أولاد'] + df['_بدل_زواج']
    
    # Amount due
    df['الفرق المستحق'] = df['الإشتراكات 25.5%'] - df['التعويضات العائلية المدفوعة']
    
    # Tax deductions (yearly amounts = quarterly * 4)
    df['_تنزيل_أولاد'] = df['عدد الأولاد'] * CHILD_DEDUCTION * 4
    df['_تنزيل_زواج'] = df['متزوج'].apply(
        lambda v: MARRIAGE_DEDUCTION * 4 if str(v).lower() == 'yes' else 0
    )
    
    def personal_deduction_yearly(foreign_val):
        f = str(foreign_val).upper()
        if f in ('YES', 'NO'):
            return PERSONAL_DEDUCTION_RESIDENT * 4
        elif f == 'F':
            return PERSONAL_DEDUCTION_F * 4
        else:
            return 0
    
    df['_تنزيل_شخصي'] = df['اجنبي'].apply(personal_deduction_yearly)
    df['التنزيل العائلي'] = df['_تنزيل_أولاد'] + df['_تنزيل_زواج'] + df['_تنزيل_شخصي']
    
    # Taxable amount
    df['المبلغ الخاضع'] = np.maximum(df['مجموع الرواتب'] - df['التنزيل العائلي'], 0)
    
    # Tax
    df['الضريبة'] = df['المبلغ الخاضع'] * TAX_RATE
    
    # Transport allowance (yearly)
    transport_yearly = TRANSPORT_PER_DAY * WORK_DAYS_PER_MONTH * 12
    df['بدل نقل'] = df['اسم الأجير'].apply(
        lambda name: transport_yearly if pd.notna(name) and str(name).strip() != '' else 0
    )
    
    display_cols = [
        'رقم',
        'اسم الأجير',
        'تاريخ بدء العمل',
        'اجنبي',
        'متزوج',
        'عدد الأولاد',
        'الراتب الشهري',
        'مجموع الرواتب',
        'الإشتراكات 25.5%',
        'التعويضات العائلية المدفوعة',
        'الفرق المستحق',
        'التنزيل العائلي',
        'المبلغ الخاضع',
        'الضريبة',
        'بدل نقل',
    ]
    
    return df[display_cols].copy()


# ---------------------------------------------------------------------------
# Helper functions for interactive use
# ---------------------------------------------------------------------------
_inputs = None  # cached inputs DataFrame


def get_inputs():
    """Get or create the inputs DataFrame."""
    global _inputs
    if _inputs is None:
        _inputs = load_inputs()
    return _inputs


def add_employee(name, monthly_salary, start_date=None, foreign='no', 
                 married='no', children=0):
    """
    Add a new employee to the inputs and recalculate.
    
    Args:
        name: Employee name (اسم الأجير)
        monthly_salary: Monthly salary (الراتب الشهري) in LBP
        start_date: Start date (optional)
        foreign: 'yes', 'no', or 'F' (اجنبي)
        married: 'yes' or 'no' (متزوج)
        children: Number of children (عدد الأولاد)
    
    Returns:
        Updated quarterly DataFrame
    """
    global _inputs, df, df_monthly, df_yearly
    
    inputs = get_inputs()
    next_num = inputs['رقم'].max() + 1 if len(inputs) > 0 else 1
    
    new_row = pd.DataFrame([{
        'رقم': int(next_num),
        'اسم الأجير': name,
        'تاريخ بدء العمل': start_date,
        'الراتب الشهري': monthly_salary,
        'اجنبي': str(foreign).upper(),
        'عدد الأولاد_input': children,
        'متزوج_input': str(married).lower(),
    }])
    
    _inputs = pd.concat([inputs, new_row], ignore_index=True)
    return recalculate()


def recalculate():
    """Recalculate all formulas from current inputs."""
    global df, df_monthly, df_yearly, summary
    
    inputs = get_inputs()
    df_monthly = calculate_quarterly(inputs)
    df_yearly = calculate_yearly(inputs)
    summary = calculate_summary(df_monthly)
    df = df_monthly
    return df


def format_lbp(value):
    """Format a number as Lebanese Pounds."""
    if pd.isna(value) or value == 0:
        return '0'
    return f'{value:,.0f} ل.ل'


def show_employee(num):
    """Show detailed breakdown for one employee by row number."""
    row = df_monthly[df_monthly['رقم'] == num]
    if row.empty:
        print(f'Employee #{num} not found.')
        return
    
    r = row.iloc[0]
    print(f'\n{"="*50}')
    print(f'  Employee #{num}: {r["اسم الأجير"]}')
    print(f'{"="*50}')
    print(f'  Start date:      {r["تاريخ بدء العمل"]}')
    print(f'  Foreign:         {r["اجنبي"]}')
    print(f'  Married:         {r["متزوج"]}')
    print(f'  Children:        {r["عدد الأولاد"]}')
    print(f'  Monthly salary:  {format_lbp(r["الراتب الشهري"])}')
    print(f'{"─"*50}')
    print(f'  Quarterly salary:          {format_lbp(r["مجموع الرواتب"])}')
    print(f'  End of service (8.5%):     {format_lbp(r["نهاية الخدمة 8.5%"])}')
    print(f'  Family allowances (6%):    {format_lbp(r["تعويضات عائلية 6%"])}')
    print(f'  Sickness & maternity (11%):{format_lbp(r["المرض و الامومة 11%"])}')
    print(f'  Total contributions:       {format_lbp(r["مجموع الاشتراكات"])}')
    print(f'  Family allowances paid:    {format_lbp(r["التعويضات العائلية المدفوعة"])}')
    print(f'  Amount due:                {format_lbp(r["الفرق المستحق"])}')
    print(f'{"─"*50}')
    print(f'  Family deduction:          {format_lbp(r["التنزيل العائلي"])}')
    print(f'  Taxable amount:            {format_lbp(r["المبلغ الخاضع"])}')
    print(f'  Tax (2%):                  {format_lbp(r["الضريبة"])}')
    print(f'  Transport allowance:       {format_lbp(r["بدل نقل"])}')
    print(f'{"="*50}')


def show_summary():
    """Display the summary calculations."""
    s = summary
    print(f'\n{"="*50}')
    print(f'  ملخص الرواتب - Salary Summary')
    print(f'{"="*50}')
    for key, val in s.items():
        print(f'  {key}: {format_lbp(val)}')
    print(f'{"="*50}')


# ---------------------------------------------------------------------------
# Load and calculate on import
# ---------------------------------------------------------------------------
_inputs = load_inputs()
df_monthly = calculate_quarterly(_inputs)
df_yearly = calculate_yearly(_inputs)
summary = calculate_summary(df_monthly)
df = df_monthly  # default alias


# ---------------------------------------------------------------------------
# Main output
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    _setup_encoding()
    print('=' * 70)
    print('  جدول رواتب و أجور 2026 - Salary & Wages Calculator')
    print('  All Excel formulas replicated in Python')
    print('=' * 70)
    
    employees_with_data = df_monthly[df_monthly['اسم الأجير'].notna()]
    print(f'\n📋 Employees with data: {len(employees_with_data)} / {len(df_monthly)}')
    
    print('\n--- Quarterly Payroll (شهري) ---')
    print(df_monthly.to_string())
    
    print('\n--- Yearly Payroll (سنوي) ---')
    print(df_yearly.to_string())
    
    print()
    show_summary()
    
    print('\n' + '=' * 70)
    print('💡 Interactive mode: python -X utf8 -i salary_data.py')
    print()
    print('   Commands:')
    print('     add_employee("أحمد", 10000000, married="yes", children=2)')
    print('     recalculate()            # recalculate after changes')
    print('     show_employee(1)         # detailed breakdown')
    print('     show_summary()           # salary summary')
    print('     df                       # view quarterly table')
    print('     df_yearly                # view yearly table')
    print('=' * 70)
