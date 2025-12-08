# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    # MOMO specific fields
    momo_merchant_id = fields.Char(
        string='MOMO Merchant ID',
        help='Your MOMO merchant identifier'
    )
    
    momo_qr_image = fields.Binary(
        string='MOMO QR Code Image',
        help='QR code image to display for MOMO payment'
    )
    
    momo_phone_number = fields.Char(
        string='MOMO Phone Number',
        help='Merchant phone number for MOMO payment'
    )
    
    def _get_payment_terminal_selection(self):
        return super()._get_payment_terminal_selection() + [('momo', 'MOMO')]
