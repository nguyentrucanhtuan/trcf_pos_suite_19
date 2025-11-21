from odoo import http
from odoo.http import request
import pytz
from datetime import datetime, time

class TrcfExpenseController(http.Controller):

    @http.route('/trcf_fnb_inventory/expense_list', type='http', auth='user', website=False)
    def expense_list(self, **kw):
        
        # Get user's timezone
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        
        # Get today's date in user's timezone
        today_local = datetime.now(user_tz).date()
        
        # Create datetime range for today (start of day to end of day in user's timezone)
        dt_start = datetime.combine(today_local, time.min)
        dt_end = datetime.combine(today_local, time.max)
        
        # Convert to UTC for database query
        dt_start_utc = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)
        dt_end_utc = user_tz.localize(dt_end).astimezone(pytz.utc).replace(tzinfo=None)
        
        expenses = []

        # Lấy các báo cáo chi phí trong ngày hiện tại
        hr_expenses = request.env['hr.expense'].sudo().search([
            ('create_date', '>=', dt_start_utc),
            ('create_date', '<=', dt_end_utc),
        ], order='create_date desc')

        for expense in hr_expenses:
            # Format create_date to local timezone
            create_date_formatted = ''
            if expense.create_date:
                # Get user's timezone (default to UTC if not set)
                user_tz = pytz.timezone(request.env.user.tz or 'UTC')
                # Convert UTC datetime to user's timezone
                create_date_local = pytz.utc.localize(expense.create_date).astimezone(user_tz)
                # Format to Vietnamese datetime format
                create_date_formatted = create_date_local.strftime('%d/%m/%Y %H:%M:%S')
                
            # Format amount with thousand separators
            formatted_amount = '{:,.0f}'.format(expense.total_amount).replace(',', '.')
            
            expenses.append({
                'id': expense.id,
                'expense_type': expense.product_id.name if expense.product_id else 'N/A', # Tên sản phẩm/dịch vụ
                'expense_name': expense.name, # Tên của báo cáo chi phí
                'expense_date': expense.date, # Ngày của chi phí
                'expense_total_amount': expense.total_amount, # Tổng số tiền
                'expense_total_amount_formatted': formatted_amount, # Tổng số tiền đã định dạng
                'expense_currency': expense.currency_id.symbol if expense.currency_id else '', # Ký hiệu tiền tệ
                'expense_employee': expense.employee_id.name if expense.employee_id else 'N/A', # Tên nhân viên
                'payment_method': expense.payment_method_line_id.name if expense.payment_method_line_id else 'N/A', # Phương thức thanh toán
                'create_date': create_date_formatted, # Thời gian tạo
            })
        
        # Calculate statistics
        total_amount = sum(exp['expense_total_amount'] for exp in expenses)
        total_amount_formatted = '{:,.0f}'.format(total_amount).replace(',', '.')
        
        # Group by payment method
        payment_method_stats = {}
        for exp in expenses:
            pm = exp['payment_method']
            if pm not in payment_method_stats:
                payment_method_stats[pm] = 0
            payment_method_stats[pm] += exp['expense_total_amount']
        
        # Format payment method stats
        payment_method_list = []
        for pm, amount in payment_method_stats.items():
            payment_method_list.append({
                'name': pm,
                'amount': amount,
                'amount_formatted': '{:,.0f}'.format(amount).replace(',', '.')
            })
        
        # Get currency symbol (assume all expenses use same currency)
        currency_symbol = expenses[0]['expense_currency'] if expenses else '₫'

        # Truyền dữ liệu chi phí vào template
        return request.render('trcf_fnb_inventory.expense_list_template', {
            'total_expenses': expenses,
            'total_amount': total_amount,
            'total_amount_formatted': total_amount_formatted,
            'payment_method_stats': payment_method_list,
            'currency_symbol': currency_symbol,
            # 'today': today.strftime('%d/%m/%Y')
        })

    @http.route('/trcf_fnb_inventory/expense_add', type='http', auth='user', website=False, methods=['GET', 'POST'])
    def expense_add(self, **kw):
        error_message = False
        
        # Fetch expense products for the dropdown (both GET and POST might need this if we re-render on error)
        expense_products = request.env['product.product'].sudo().search([
            ('can_be_expensed', '=', True)
        ])
        
        # Fetch payment method lines for company_account (outbound payments)
        payment_method_lines = request.env['account.payment.method.line'].sudo().search([
            ('payment_type', '=', 'outbound'),
            ('company_id', '=', request.env.company.id)
        ])

        if request.httprequest.method == 'POST':
            try:
                # Lấy thông tin từ form
                expense_type_id = int(request.params.get('expense_type'))
                expense_name = request.params.get('expense_name')
                expense_amount = float(request.params.get('expense_amount'))
                payment_method_line_id = int(request.params.get('payment_method_line_id')) if request.params.get('payment_method_line_id') else False
                
                # Find employee for current user in the current company
                employee = request.env['hr.employee'].sudo().search([
                    ('user_id', '=', request.env.user.id),
                    ('company_id', '=', request.env.company.id)
                ], limit=1)
                
                if not employee:
                    raise Exception("Không tìm thấy thông tin nhân viên cho tài khoản này.")

                # Create expense
                expense_vals = {
                    'name': expense_name,
                    'product_id': expense_type_id,
                    'total_amount_currency': expense_amount,
                    'quantity': 1,
                    'employee_id': employee.id,
                    'payment_mode': 'company_account',
                    'currency_id': request.env.company.currency_id.id,
                    'state': 'draft',
                }
                
                if payment_method_line_id:
                    expense_vals['payment_method_line_id'] = payment_method_line_id
                
                # Optional: Add description or other fields if needed
                
                expense = request.env['hr.expense'].sudo().create(expense_vals)

                return request.redirect('/trcf_fnb_inventory/expense_list?success=1')

            except Exception as e:
                error_message = f"Đã có lỗi xảy ra: {str(e)}"
                # print("error_message", error_message) # Use logging instead of print in production

        return request.render('trcf_fnb_inventory.expense_form_template', {
            'expense_products': expense_products,
            'payment_method_lines': payment_method_lines,
            'error_message': error_message
        })