from odoo import api, models, fields


class TrcfPosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    # MoMo QR Code configuration
    momo_qr_code = fields.Binary(
        string="Mã QR MoMo",
        help="Ảnh mã QR MoMo để hiển thị khi thanh toán. "
             "Có thể lấy từ ứng dụng MoMo > Ví của tôi > Nhận tiền"
    )

    @api.model
    def _load_pos_data_fields(self, config):
        """Add momo_qr_code to the list of fields loaded in POS"""
        fields = super()._load_pos_data_fields(config)
        fields.append('momo_qr_code')
        return fields

    def _get_payment_terminal_selection(self):
        """Add TRCF MoMo terminal to the list of available terminals"""
        return super()._get_payment_terminal_selection() + [('trcf_momo', 'MoMo QR')]