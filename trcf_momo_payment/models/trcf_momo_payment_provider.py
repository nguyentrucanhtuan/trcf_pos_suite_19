from odoo import models, fields

class TrcfMomoPaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('trcf_momo_provider', "TRCF MoMo Provider")],
        ondelete={'trcf_momo_provider': 'set default'}
    )