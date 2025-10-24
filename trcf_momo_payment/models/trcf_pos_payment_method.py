from odoo import models, fields

class TrcfPosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'
    
    def _get_payment_terminal_selection(self):
        return super()._get_payment_terminal_selection() + [('trcf_momo_terminal', 'TRCF MoMo Terminal')]