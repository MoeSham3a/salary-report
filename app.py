"""
Flask Application — Multi-company, per-quarter payroll system.
"""
from flask import Flask, render_template, jsonify, request, send_file
import database as db
from salary_engine import calculate_employee_quarterly, calculate_employee_yearly, calculate_summary
from report_generator import generate_report

app = Flask(__name__)


@app.before_request
def ensure_db():
    if not hasattr(app, '_db_initialized'):
        db.init_db()
        app._db_initialized = True


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/company/<int:company_id>')
def payroll_page(company_id):
    company = db.get_company(company_id)
    if not company:
        return 'Company not found', 404
    return render_template('payroll.html', company=company)


# ---------------------------------------------------------------------------
# Company API
# ---------------------------------------------------------------------------
@app.route('/api/companies', methods=['GET'])
def api_list_companies():
    companies = db.get_companies()
    # Add period count for each company
    for c in companies:
        periods = db.get_periods(c['id'])
        c['period_count'] = len(periods)
    return jsonify(companies)


@app.route('/api/companies', methods=['POST'])
def api_add_company():
    data = request.get_json()
    new_id = db.add_company(data)
    return jsonify({'success': True, 'id': new_id}), 201


@app.route('/api/companies/<int:company_id>', methods=['PUT'])
def api_update_company(company_id):
    data = request.get_json()
    db.update_company(company_id, data)
    return jsonify({'success': True})


@app.route('/api/companies/<int:company_id>', methods=['DELETE'])
def api_delete_company(company_id):
    db.delete_company(company_id)
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Period API
# ---------------------------------------------------------------------------
@app.route('/api/companies/<int:company_id>/periods', methods=['GET'])
def api_list_periods(company_id):
    return jsonify(db.get_periods(company_id))


@app.route('/api/companies/<int:company_id>/periods', methods=['POST'])
def api_create_period(company_id):
    data = request.get_json()
    period = db.get_or_create_period(
        company_id,
        data.get('quarter', 1),
        data.get('year', 2026)
    )
    return jsonify(period), 201


@app.route('/api/periods/<int:period_id>/copy', methods=['POST'])
def api_copy_period(period_id):
    data = request.get_json()
    source_id = data.get('source_period_id')
    if not source_id:
        return jsonify({'error': 'source_period_id required'}), 400
    count = db.copy_period(source_id, period_id)
    return jsonify({'success': True, 'copied': count})


# ---------------------------------------------------------------------------
# Employee API (per-period)
# ---------------------------------------------------------------------------
@app.route('/api/periods/<int:period_id>/employees', methods=['GET'])
def api_list_employees(period_id):
    employees = db.get_employees(period_id)
    period = db.get_period(period_id)
    if not period:
        return jsonify([])

    from salary_engine import get_minimum_wage
    min_wage = get_minimum_wage(period['quarter'], period['year'])

    result = []
    for emp in employees:
        calc = calculate_employee_quarterly(emp, period['quarter'], period['year'])
        combined = {**emp, **calc}
        combined['minimum_wage'] = min_wage
        salary = emp.get('monthly_salary', 0) or 0
        has_name = bool(emp.get('name') and str(emp['name']).strip())
        combined['below_minimum'] = has_name and salary > 0 and salary < min_wage
        result.append(combined)
    return jsonify(result)


@app.route('/api/periods/<int:period_id>/employees', methods=['POST'])
def api_add_employee(period_id):
    data = request.get_json()
    new_id = db.add_employee(period_id, data)
    return jsonify({'success': True, 'id': new_id}), 201


@app.route('/api/employees/<int:employee_id>', methods=['PUT'])
def api_update_employee(employee_id):
    data = request.get_json()
    db.update_employee(employee_id, data)
    return jsonify({'success': True})


@app.route('/api/employees/<int:employee_id>', methods=['DELETE'])
def api_delete_employee(employee_id):
    db.delete_employee(employee_id)
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Summary API
# ---------------------------------------------------------------------------
@app.route('/api/periods/<int:period_id>/summary', methods=['GET'])
def api_summary(period_id):
    period = db.get_period(period_id)
    if not period:
        return jsonify({})
    employees = db.get_employees(period_id)
    summary = calculate_summary(employees, 'quarter', period['quarter'], period['year'])
    return jsonify(summary)


# ---------------------------------------------------------------------------
# Report Download
# ---------------------------------------------------------------------------
@app.route('/api/periods/<int:period_id>/report', methods=['GET'])
def api_report(period_id):
    period = db.get_period(period_id)
    if not period:
        return 'Period not found', 404

    company = db.get_company(period['company_id'])
    employees = db.get_employees(period_id)

    output = generate_report(employees, company, 'quarter')
    filename = f"payroll_Q{period['quarter']}_{period['year']}.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/companies/<int:company_id>/yearly-report', methods=['GET'])
def api_yearly_report(company_id):
    year = request.args.get('year', 2026, type=int)
    company = db.get_company(company_id)
    if not company:
        return 'Company not found', 404

    # Aggregate all employees from all quarters of the year
    all_employees = []
    for q in range(1, 5):
        period = db.get_or_create_period(company_id, q, year)
        employees = db.get_employees(period['id'])
        all_employees.extend(employees)

    output = generate_report(all_employees, company, 'year')
    filename = f"payroll_yearly_{year}.xlsx"

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    import sys, io
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except Exception:
            pass

    db.init_db()
    print('\n' + '=' * 50)
    print('  Salary App — http://localhost:5000')
    print('=' * 50 + '\n')
    app.run(debug=True, host='0.0.0.0', port=5000)
