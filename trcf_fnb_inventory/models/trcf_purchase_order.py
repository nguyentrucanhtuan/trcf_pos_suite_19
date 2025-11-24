from odoo import models, fields, api


class TrcfPurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    trcf_payment_method_id = fields.Many2one(
        'pos.payment.method',
        string='Phương thức thanh toán',
        help='Phương thức thanh toán cho đơn mua hàng'
    )
    
    trcf_payment_status = fields.Selection([
        ('unpaid', 'Chưa thanh toán'),
        ('paid', 'Đã thanh toán')
    ], string='Trạng thái thanh toán', default='unpaid', required=True)
    
    trcf_payment_date = fields.Datetime(
        string='Ngày thanh toán',
        help='Ngày và giờ thực hiện thanh toán'
    )
    
    @api.onchange('trcf_payment_status')
    def _onchange_trcf_payment_status(self):
        """Tự động set payment_date khi status = paid"""
        if self.trcf_payment_status == 'paid' and not self.trcf_payment_date:
            self.trcf_payment_date = fields.Datetime.now()
        elif self.trcf_payment_status == 'unpaid':
            self.trcf_payment_date = False
