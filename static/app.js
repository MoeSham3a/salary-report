/**
 * Payroll Page Logic — Per-company, per-quarter employee management.
 * COMPANY_ID is set by the template.
 */

let employees = [];
let currentPeriodId = null;
let currentQuarter = 1;
let currentYear = 2026;
let debounceTimer = null;

// ============================================================
// API
// ============================================================
async function api(url, method = 'GET', body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    return res.json();
}

function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return '0';
    return Math.round(num).toLocaleString('en-US');
}

function showToast(msg, type = 'success') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = `toast ${type} show`;
    setTimeout(() => { t.className = 'toast'; }, 2500);
}

// ============================================================
// Period Management
// ============================================================
async function loadPeriod() {
    // Create or get the period for current quarter/year
    const period = await api(`/api/companies/${COMPANY_ID}/periods`, 'POST', {
        quarter: currentQuarter,
        year: currentYear,
    });
    currentPeriodId = period.id;
    await loadEmployees();
}

async function loadEmployees() {
    if (!currentPeriodId) return;
    employees = await api(`/api/periods/${currentPeriodId}/employees`);
    renderTable();
    await loadSummary();
}

async function loadSummary() {
    if (!currentPeriodId) return;
    const summary = await api(`/api/periods/${currentPeriodId}/summary`);

    const totalSalaries = employees.reduce((s, e) => s + (e.total_salary || 0), 0);
    const totalTransport = employees.reduce((s, e) => s + (e.transport || 0), 0);

    document.getElementById('totalSalaries').textContent = formatNumber(totalSalaries);
    document.getElementById('totalEmployees').textContent = employees.filter(e => e.name && e.name.trim()).length;
    document.getElementById('totalTax').textContent = formatNumber(summary['الضريبة المتوجبة'] || 0);
    document.getElementById('totalTransport').textContent = formatNumber(totalTransport);

    document.getElementById('sum_salaries').textContent = formatNumber(summary['مجموع الرواتب']);
    document.getElementById('sum_benefits').textContent = formatNumber(summary['المنافع النقدية والعينية']);
    document.getElementById('sum_total_paid').textContent = formatNumber(summary['مجموع المبالغ المدفوعة']);
    document.getElementById('sum_transport').textContent = formatNumber(summary['تعويضات نقل وانتقال']);
    document.getElementById('sum_family').textContent = formatNumber(summary['التعويضات العائلية']);
    document.getElementById('sum_net').textContent = formatNumber(summary['مجموع الرواتب_net']);
    document.getElementById('sum_deductions').textContent = formatNumber(summary['التنزيل العائلي']);
    document.getElementById('sum_taxable').textContent = formatNumber(summary['المبلغ الخاضع']);
    document.getElementById('sum_tax_due').textContent = formatNumber(summary['الضريبة المتوجبة']);
}

// ============================================================
// Table
// ============================================================
function renderTable() {
    const tbody = document.getElementById('employeeTableBody');
    tbody.innerHTML = '';

    employees.forEach(emp => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="col-actions">
                <button class="btn btn-danger" onclick="deleteEmployee(${emp.id})" title="حذف">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/><path d="M19 6l-2 14H7L5 6"/>
                        <path d="M10 11v6"/><path d="M14 11v6"/>
                    </svg>
                </button>
            </td>
            <td class="row-num">${emp.row_number}</td>
            <td><input class="cell-input" type="text" value="${emp.name || ''}" data-id="${emp.id}" data-field="name" placeholder="اسم الموظف"></td>
            <td><input class="cell-input" type="date" value="${emp.start_date || ''}" data-id="${emp.id}" data-field="start_date"></td>
            <td>
                <select class="cell-select" data-id="${emp.id}" data-field="is_foreign">
                    <option value="no" ${emp.is_foreign === 'no' ? 'selected' : ''}>لا</option>
                    <option value="yes" ${emp.is_foreign === 'yes' ? 'selected' : ''}>نعم</option>
                    <option value="F" ${emp.is_foreign === 'F' ? 'selected' : ''}>F</option>
                </select>
            </td>
            <td>
                <select class="cell-select" data-id="${emp.id}" data-field="is_married">
                    <option value="no" ${emp.is_married === 'no' ? 'selected' : ''}>لا</option>
                    <option value="yes" ${emp.is_married === 'yes' ? 'selected' : ''}>نعم</option>
                </select>
            </td>
            <td><input class="cell-input" type="number" value="${emp.num_children || 0}" min="0" max="20" data-id="${emp.id}" data-field="num_children" style="width:60px"></td>
            <td class="${emp.below_minimum ? 'cell-warning' : ''}">
                <input class="cell-input" type="number" value="${emp.monthly_salary || 0}" min="0" data-id="${emp.id}" data-field="monthly_salary" style="width:120px">
                ${emp.below_minimum ? `<span class="wage-warning" title="الحد الأدنى: ${formatNumber(emp.minimum_wage)} ل.ل">⚠️ أقل من الحد الأدنى</span>` : ''}
            </td>
            <td class="computed-cell">${formatNumber(emp.total_salary)}</td>
            <td class="computed-cell">${formatNumber(emp.end_of_service)}</td>
            <td class="computed-cell">${formatNumber(emp.family_6)}</td>
            <td class="computed-cell">${formatNumber(emp.sickness_11)}</td>
            <td class="computed-cell">${formatNumber(emp.total_contributions)}</td>
            <td class="computed-cell">${formatNumber(emp.family_paid)}</td>
            <td class="computed-cell">${formatNumber(emp.amount_due)}</td>
            <td class="computed-cell">${formatNumber(emp.family_deduction)}</td>
            <td class="computed-cell">${formatNumber(emp.taxable)}</td>
            <td class="computed-cell">${formatNumber(emp.tax)}</td>
            <td class="computed-cell">${formatNumber(emp.transport)}</td>
        `;
        tbody.appendChild(tr);
    });

    // Attach listeners
    tbody.querySelectorAll('.cell-input, .cell-select').forEach(el => {
        el.addEventListener('change', handleCellEdit);
        if (el.type === 'number' || el.type === 'text') {
            el.addEventListener('input', () => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => handleCellEdit({ target: el }), 600);
            });
        }
    });
}

// ============================================================
// Inline Edit
// ============================================================
async function handleCellEdit(e) {
    const el = e.target;
    const id = parseInt(el.dataset.id);
    const field = el.dataset.field;
    let value = el.value;

    if (field === 'monthly_salary' || field === 'num_children') {
        value = parseFloat(value) || 0;
    }

    const emp = employees.find(e => e.id === id);
    if (!emp) return;
    emp[field] = value;

    const payload = {
        name: emp.name || '',
        start_date: emp.start_date || '',
        monthly_salary: parseFloat(emp.monthly_salary) || 0,
        is_foreign: emp.is_foreign || 'no',
        is_married: emp.is_married || 'no',
        num_children: parseInt(emp.num_children) || 0,
    };

    await api(`/api/employees/${id}`, 'PUT', payload);
    await loadEmployees();
}

// ============================================================
// CRUD
// ============================================================
async function deleteEmployee(id) {
    await api(`/api/employees/${id}`, 'DELETE');
    showToast('تم حذف الموظف');
    await loadEmployees();
}

async function saveNewEmployee() {
    const name = document.getElementById('empName').value.trim();
    if (!name) { showToast('يرجى إدخال اسم الموظف', 'error'); return; }

    const payload = {
        name,
        start_date: document.getElementById('empStartDate').value || '',
        monthly_salary: parseFloat(document.getElementById('empSalary').value) || 0,
        is_foreign: document.getElementById('empForeign').value,
        is_married: document.getElementById('empMarried').value,
        num_children: parseInt(document.getElementById('empChildren').value) || 0,
    };

    await api(`/api/periods/${currentPeriodId}/employees`, 'POST', payload);
    closeEmpModal();
    showToast('تم إضافة الموظف بنجاح');
    await loadEmployees();

    document.getElementById('empName').value = '';
    document.getElementById('empStartDate').value = '';
    document.getElementById('empSalary').value = '';
    document.getElementById('empForeign').value = 'no';
    document.getElementById('empMarried').value = 'no';
    document.getElementById('empChildren').value = '0';
}

// ============================================================
// Copy from Previous Quarter
// ============================================================
async function copyFromPrevious() {
    // Determine previous quarter
    let prevQ = currentQuarter - 1;
    let prevY = currentYear;
    if (prevQ < 1) { prevQ = 4; prevY -= 1; }

    // Get or create source period
    const sourcePeriod = await api(`/api/companies/${COMPANY_ID}/periods`, 'POST', {
        quarter: prevQ, year: prevY
    });

    if (!sourcePeriod.id) {
        showToast('لا توجد بيانات في الفصل السابق', 'error');
        return;
    }

    const sourceEmployees = await api(`/api/periods/${sourcePeriod.id}/employees`);
    if (sourceEmployees.length === 0) {
        showToast(`الفصل ${prevQ} / ${prevY} فارغ`, 'error');
        return;
    }

    if (employees.length > 0) {
        if (!confirm(`سيتم استبدال البيانات الحالية (${employees.length} موظف) ببيانات الفصل ${prevQ}. متابعة؟`)) return;
    }

    await api(`/api/periods/${currentPeriodId}/copy`, 'POST', {
        source_period_id: sourcePeriod.id
    });
    showToast(`تم نسخ ${sourceEmployees.length} موظف من الفصل ${prevQ}`);
    await loadEmployees();
}

// ============================================================
// Modal
// ============================================================
function openEmpModal() {
    document.getElementById('empModalOverlay').classList.add('active');
    setTimeout(() => document.getElementById('empName').focus(), 100);
}

function closeEmpModal() {
    document.getElementById('empModalOverlay').classList.remove('active');
}

// ============================================================
// Report
// ============================================================
function downloadReport() {
    if (!currentPeriodId) return;
    window.location.href = `/api/periods/${currentPeriodId}/report`;
    showToast('جاري تحميل التقرير...');
}

// ============================================================
// Quarter Tabs
// ============================================================
function switchQuarter(q) {
    currentQuarter = q;
    document.querySelectorAll('.period-tab').forEach(tab => {
        tab.classList.toggle('active', parseInt(tab.dataset.q) === q);
    });
    loadPeriod();
}

// ============================================================
// Init
// ============================================================
document.addEventListener('DOMContentLoaded', async () => {
    // Load period
    await loadPeriod();

    // Quarter tabs
    document.querySelectorAll('.period-tab').forEach(tab => {
        tab.addEventListener('click', () => switchQuarter(parseInt(tab.dataset.q)));
    });

    // Year change
    document.getElementById('periodYear').addEventListener('change', (e) => {
        currentYear = parseInt(e.target.value) || 2026;
        loadPeriod();
    });

    // Buttons
    document.getElementById('addEmployeeBtn').addEventListener('click', openEmpModal);
    document.getElementById('empModalClose').addEventListener('click', closeEmpModal);
    document.getElementById('empModalCancel').addEventListener('click', closeEmpModal);
    document.getElementById('empModalSave').addEventListener('click', saveNewEmployee);
    document.getElementById('downloadReport').addEventListener('click', downloadReport);
    document.getElementById('copyPrevBtn').addEventListener('click', copyFromPrevious);

    // Modal overlay close
    document.getElementById('empModalOverlay').addEventListener('click', e => {
        if (e.target === e.currentTarget) closeEmpModal();
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') closeEmpModal();
        if (e.key === 'Enter' && document.getElementById('empModalOverlay').classList.contains('active')) saveNewEmployee();
    });
});
