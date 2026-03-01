"""
SQLite Database Layer — Multi-company, per-quarter employee data.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'payroll.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT '',
            financial_number TEXT DEFAULT '',
            social_security_number TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS payroll_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            quarter INTEGER NOT NULL,
            year INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company_id, quarter, year)
        );

        CREATE TABLE IF NOT EXISTS employee_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_id INTEGER NOT NULL REFERENCES payroll_periods(id) ON DELETE CASCADE,
            row_number INTEGER NOT NULL,
            name TEXT NOT NULL DEFAULT '',
            start_date TEXT DEFAULT '',
            monthly_salary REAL DEFAULT 0,
            is_foreign TEXT DEFAULT 'no',
            is_married TEXT DEFAULT 'no',
            num_children INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------
def get_companies():
    conn = get_db()
    rows = conn.execute("SELECT * FROM companies ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_company(company_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_company(data):
    conn = get_db()
    conn.execute("""
        INSERT INTO companies (name, financial_number, social_security_number)
        VALUES (?, ?, ?)
    """, (
        data.get('name', ''),
        data.get('financial_number', ''),
        data.get('social_security_number', ''),
    ))
    conn.commit()
    new_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()['id']
    conn.close()
    return new_id


def update_company(company_id, data):
    conn = get_db()
    conn.execute("""
        UPDATE companies SET name=?, financial_number=?, social_security_number=?
        WHERE id=?
    """, (
        data.get('name', ''),
        data.get('financial_number', ''),
        data.get('social_security_number', ''),
        company_id,
    ))
    conn.commit()
    conn.close()


def delete_company(company_id):
    conn = get_db()
    conn.execute("DELETE FROM companies WHERE id=?", (company_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Payroll Periods
# ---------------------------------------------------------------------------
def get_periods(company_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT p.*, COUNT(e.id) as employee_count
        FROM payroll_periods p
        LEFT JOIN employee_entries e ON e.period_id = p.id
        WHERE p.company_id = ?
        GROUP BY p.id
        ORDER BY p.year DESC, p.quarter DESC
    """, (company_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_period(period_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM payroll_periods WHERE id=?", (period_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_or_create_period(company_id, quarter, year):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM payroll_periods WHERE company_id=? AND quarter=? AND year=?",
        (company_id, quarter, year)
    ).fetchone()
    
    if row:
        conn.close()
        return dict(row)
    
    conn.execute(
        "INSERT INTO payroll_periods (company_id, quarter, year) VALUES (?, ?, ?)",
        (company_id, quarter, year)
    )
    conn.commit()
    new_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()['id']
    row = conn.execute("SELECT * FROM payroll_periods WHERE id=?", (new_id,)).fetchone()
    conn.close()
    return dict(row)


def copy_period(source_period_id, target_period_id):
    """Copy all employee entries from one period to another."""
    conn = get_db()
    # Clear target first
    conn.execute("DELETE FROM employee_entries WHERE period_id=?", (target_period_id,))
    # Copy
    conn.execute("""
        INSERT INTO employee_entries (period_id, row_number, name, start_date,
                                       monthly_salary, is_foreign, is_married, num_children)
        SELECT ?, row_number, name, start_date,
               monthly_salary, is_foreign, is_married, num_children
        FROM employee_entries WHERE period_id=?
        ORDER BY row_number
    """, (target_period_id, source_period_id))
    conn.commit()
    count = conn.execute(
        "SELECT COUNT(*) as c FROM employee_entries WHERE period_id=?",
        (target_period_id,)
    ).fetchone()['c']
    conn.close()
    return count


# ---------------------------------------------------------------------------
# Employee Entries (per-period)
# ---------------------------------------------------------------------------
def get_employees(period_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM employee_entries WHERE period_id=? ORDER BY row_number",
        (period_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_employee(period_id, data):
    conn = get_db()
    max_row = conn.execute(
        "SELECT COALESCE(MAX(row_number), 0) as m FROM employee_entries WHERE period_id=?",
        (period_id,)
    ).fetchone()['m']

    conn.execute("""
        INSERT INTO employee_entries (period_id, row_number, name, start_date,
                                       monthly_salary, is_foreign, is_married, num_children)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        period_id,
        max_row + 1,
        data.get('name', ''),
        data.get('start_date', ''),
        data.get('monthly_salary', 0),
        data.get('is_foreign', 'no'),
        data.get('is_married', 'no'),
        data.get('num_children', 0),
    ))
    conn.commit()
    new_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()['id']
    conn.close()
    return new_id


def update_employee(employee_id, data):
    conn = get_db()
    conn.execute("""
        UPDATE employee_entries SET
            name=?, start_date=?, monthly_salary=?,
            is_foreign=?, is_married=?, num_children=?
        WHERE id=?
    """, (
        data.get('name', ''),
        data.get('start_date', ''),
        data.get('monthly_salary', 0),
        data.get('is_foreign', 'no'),
        data.get('is_married', 'no'),
        data.get('num_children', 0),
        employee_id,
    ))
    conn.commit()
    conn.close()


def delete_employee(employee_id):
    conn = get_db()
    # Get period_id before delete
    row = conn.execute("SELECT period_id FROM employee_entries WHERE id=?", (employee_id,)).fetchone()
    if not row:
        conn.close()
        return
    period_id = row['period_id']
    conn.execute("DELETE FROM employee_entries WHERE id=?", (employee_id,))
    # Re-number
    rows = conn.execute(
        "SELECT id FROM employee_entries WHERE period_id=? ORDER BY row_number",
        (period_id,)
    ).fetchall()
    for i, r in enumerate(rows, 1):
        conn.execute("UPDATE employee_entries SET row_number=? WHERE id=?", (i, r['id']))
    conn.commit()
    conn.close()
