# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Thông tin MInvoice\
    minvoice_tax_code = fields.Char(
        string='Mã số thuế',
        config_parameter='trcf_minvoice.tax_code',
        help='Mã số thuế 10 hoặc 13 số'
    )
    
    minvoice_username = fields.Char(
        string='Username',
        config_parameter='trcf_minvoice.username'
    )
    
    minvoice_password = fields.Char(
        string='Password',
        config_parameter='trcf_minvoice.password'
    )

    minvoice_invoice_series = fields.Char(
        string='Ký hiệu hóa đơn',
        config_parameter='trcf_minvoice.invoice_series',
        help='Ví dụ: 1C25TYY'
    )