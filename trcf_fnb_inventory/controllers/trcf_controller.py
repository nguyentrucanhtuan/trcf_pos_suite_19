import pytz
from datetime import datetime, time, timedelta
from odoo import http
from odoo.http import request

class TrcfFnbInventory(http.Controller):

    @http.route('/trcf_fnb_inventory/daily_report', type='http', auth='user', website=False)
    def daily_report(self, filter_type='today', date_from=None, date_to=None, **kw):

        # --- BƯỚC 1: LẤY TIMEZONE CỦA USER ---
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        # Lấy thời gian hiện tại theo giờ của User (Ví dụ: GMT+7)
        now_user_tz = datetime.now(user_tz)
        today = now_user_tz.date()

        # --- BƯỚC 2: XÁC ĐỊNH KHOẢNG THỜI GIAN (USER TIME) ---
        if filter_type == 'today':
            current_start = today
            current_end = today
        elif filter_type == 'week':
            current_start = today - timedelta(days=today.weekday())
            current_end = today
        elif filter_type == 'month':
            current_start = today.replace(day=1)
            current_end = today
        elif filter_type == 'custom' and date_from and date_to:
            current_start = datetime.strptime(date_from, '%Y-%m-%d').date()
            current_end = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        total_pos_revenue = self.get_pos_revenue(current_start, current_end)

        # 1. Lấy tiền tệ của công ty hiện tại (VND, USD, EUR...)
        currency = request.env.company.currency_id
        # 2. Sử dụng hàm format có sẵn của Odoo
        formatted_total_revenue = currency.format(total_pos_revenue)

        vals = {
            'filter_type': filter_type,
            'date_from': date_from,
            'date_to': date_to,
            'total_pos_revenue': formatted_total_revenue
        }

        return request.render('trcf_fnb_inventory.daily_report_template', vals)

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

    def get_pos_revenue(self, start_date, end_date):
        # 1. Setup Timezone
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        
        dt_start = datetime.combine(start_date, time.min)
        dt_end = datetime.combine(end_date, time.max)
        
        # 2. XỬ LÝ LỖI "Use naive datetimes":
        # Bước 1: Localize (gán múi giờ User) -> Bước 2: Đổi sang UTC -> Bước 3: Xóa info timezone (.replace(tzinfo=None))
        dt_start_utc = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)
        dt_end_utc = user_tz.localize(dt_end).astimezone(pytz.utc).replace(tzinfo=None)

        domain = [
            ('date_order', '>=', dt_start_utc),
            ('date_order', '<=', dt_end_utc),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ]

        # 3. XỬ LÝ LỖI "read_group is deprecated":
        # Sử dụng _read_group (có dấu gạch dưới). Hàm này trả về list các tuple.
        # aggregates=['amount_total:sum'] -> Tính tổng trường amount_total
        result = request.env['pos.order']._read_group(
            domain=domain,
            aggregates=['amount_total:sum']
        )
        
        # Kết quả trả về dạng: [(Tổng_tiền,)]
        # result[0] là tuple đầu tiên, result[0][0] là giá trị sum.
        # Nếu không có đơn hàng nào, nó có thể trả về None, nên dùng (or 0)
        return result[0][0] or 0