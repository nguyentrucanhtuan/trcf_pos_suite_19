from odoo import http
from odoo.http import request

class TrcfFnbInventory(http.Controller):

    @http.route('/trcf_fnb_inventory/daily_report', type='http', auth='user', website=False)
    def daily_report(self, **kw):
        return request.render('trcf_fnb_inventory.daily_report_template')


    @http.route('/trcf_fnb_inventory/expense_list', type='http', auth='user', website=False)
    def expense_list(self, **kw):

        # today = date.today()
        expenses = []

        # Lấy các báo cáo chi phí từ hr.expense trong ngày hiện tại
        hr_expenses = request.env['hr.expense'].sudo().search([
            # ('date', '=', today),
            # ('state', 'in', ['approved', 'done']), 
        ])

        for expense in hr_expenses:
            expenses.append({
                'id': expense.id,
                'expense_type': expense.product_id.name if expense.product_id else 'N/A', # Tên sản phẩm/dịch vụ
                'expense_name': expense.name, # Tên của báo cáo chi phí
                'expense_date': expense.date, # Ngày của chi phí
                'expense_total_amount': expense.total_amount, # Tổng số tiền
                'expense_currency': expense.currency_id.symbol if expense.currency_id else '', # Ký hiệu tiền tệ
                'expense_employee': expense.employee_id.name if expense.employee_id else 'N/A', # Tên nhân viên
            })

        # Truyền dữ liệu chi phí vào template
        return request.render('trcf_fnb_inventory.expense_list_template', {
            'total_expenses': expenses,
            # 'today': today.strftime('%d/%m/%Y')
        })


    @http.route('/trcf_fnb_inventory/expense_add', type='http', auth='user', website=False, methods=['GET', 'POST'])
    def expense_add(self, **kw):
        success_message = False
        error_message = False

        if request.httprequest.method == 'POST':
            try:
                # Lấy thông tin từ form
                expense_type = int(request.params.get('expense_type'))
                expense_name = request.params.get('expense_name')
                expense_amount = float(request.params.get('expense_amount'))
                payment_method = request.params.get('payment_method')
                #employee_id = int(post.post('employee_id')) if post.post('employee_id') else False

                # Tạo phiếu chi mới
                expense = request.env['hr.expense'].sudo().create({
                    'name': expense_name,
                    'product_id': expense_type,
                    'product_uom_id': 1,
                    'company_id': 1,
                    'total_amount_currency': expense_amount,
                    'quantity': 1,
                    'employee_id': 1,
                    'payment_mode': 'company_account',
                    'currency_id' : 23,
                    'state' : 'draft',
                    'payment_method_line_id': 2
                })

                success_message = "Phiếu chi đã được tạo thành công!"
                return request.redirect('/trcf_fnb_inventory/expense_list?success=1')

            except Exception as e:
                error_message = f"Đã có lỗi xảy ra: {e}"
                print("error_message", error_message)

        return request.render('trcf_fnb_inventory.expense_form_template')