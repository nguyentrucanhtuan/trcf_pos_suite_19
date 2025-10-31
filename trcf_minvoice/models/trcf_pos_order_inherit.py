from odoo import fields, models

class TrcfPosOrder(models.Model):
    _inherit = 'pos.order'

    # Các trường thông tin hóa đơn VAT
    vat_type = fields.Selection([
        ('no_vat', 'Không xuất hoá đơn'),
        ('company', 'Doanh nghiệp'),
        ('individual', 'Cá nhân'),
    ], string='Loại VAT', default='no_vat')
    vat_email = fields.Char(string='Email')
    vat_tax_id = fields.Char(string='Mã số thuế')
    vat_customer_name = fields.Char(string='Tên khách hàng')
    vat_company_name = fields.Char(string='Tên công ty')
    vat_address = fields.Char(string='Địa chỉ')
    vat_phone = fields.Char(string='Số điện thoại')
    vat_citizen_id = fields.Char(string='Căn cước công dân')
    vat_note = fields.Text(string='Ghi chú')
    vat_account_number = fields.Char(string='Số tài khoản')
    vat_bank_name = fields.Char(string='Tên ngân hàng')
    vat_estimated_unit_code = fields.Char(string='Mã đơn vị dự toán')
    vat_passport_number = fields.Char(string='Số hộ chiếu')