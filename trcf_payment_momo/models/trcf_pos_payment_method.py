from odoo import api, models, fields
import logging

from .momo_api import MoMoAPI

_logger = logging.getLogger(__name__)


class TrcfPosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    # MoMo QR Code configuration (static QR - fallback)
    momo_qr_code = fields.Binary(
        string="Mã QR MoMo (Tĩnh)",
        help="Ảnh mã QR MoMo tĩnh để hiển thị khi không thể gọi API. "
             "Có thể lấy từ ứng dụng MoMo > Ví của tôi > Nhận tiền"
    )
    
    # MoMo API Configuration
    momo_partner_code = fields.Char(
        string="Partner Code",
        help="MoMo Partner Code từ tài khoản M4B"
    )
    momo_access_key = fields.Char(
        string="Access Key",
        help="MoMo Access Key từ tài khoản M4B"
    )
    momo_secret_key = fields.Char(
        string="Secret Key",
        help="MoMo Secret Key từ tài khoản M4B"
    )
    momo_test_mode = fields.Boolean(
        string="Chế độ Test",
        default=True,
        help="Bật để sử dụng môi trường sandbox của MoMo"
    )

    @api.model
    def _load_pos_data_fields(self, config):
        """Add momo fields to the list of fields loaded in POS"""
        fields = super()._load_pos_data_fields(config)
        fields.extend(['momo_qr_code', 'momo_test_mode'])
        return fields

    def _get_payment_terminal_selection(self):
        """Add TRCF MoMo terminal to the list of available terminals"""
        return super()._get_payment_terminal_selection() + [('trcf_momo', 'MoMo QR')]
    
    @api.model
    def create_momo_payment_rpc(self, order_id, amount, order_info=None, session_id=None, config_id=None):
        """
        RPC method to create MoMo payment from POS
        
        Args:
            order_id: POS order reference
            amount: Payment amount in VND
            order_info: Optional order description
            
        Returns:
            dict with success, qr_code_url, pay_url, deeplink, message
        """
        import uuid
        import re
        
        # Clean order_id to only contain valid characters for MoMo
        # MoMo requires: ^[0-9a-zA-Z]+([-_.:]+[0-9a-zA-Z]+)*$
        clean_order_id = re.sub(r'[^0-9a-zA-Z\-_\.:]', '', str(order_id))
        if not clean_order_id:
            clean_order_id = "ORDER"
        
        # Create unique order ID with timestamp
        momo_order_id = f"{clean_order_id}_{uuid.uuid4().hex[:8]}"
        
        _logger.info(f"Creating MoMo payment: order={momo_order_id}, amount={amount}")
        
        # Get base URL for IPN webhook
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        ipn_url = f"{base_url}/momo/ipn"
        _logger.info(f"MoMo IPN URL: {ipn_url}")
        
        # Get MoMo config from first payment method with trcf_momo terminal
        payment_method = self.search([
            ('use_payment_terminal', '=', 'trcf_momo')
        ], limit=1)
        
        # Build API instance
        if payment_method and payment_method.momo_partner_code:
            momo_api = MoMoAPI(
                partner_code=payment_method.momo_partner_code,
                access_key=payment_method.momo_access_key,
                secret_key=payment_method.momo_secret_key,
                test_mode=payment_method.momo_test_mode
            )
        else:
            # Use default test credentials
            momo_api = MoMoAPI(test_mode=True)
        
        # Create payment
        if not order_info:
            order_info = f"Thanh toan don hang {momo_order_id}"
        
        # Store pending transaction for webhook matching
        Transaction = self.env['trcf.momo.transaction'].sudo()
        Transaction.create_pending_transaction(
            pos_order_ref=str(order_id),
            momo_order_id=momo_order_id,
            amount=float(amount),
            request_id=None,
            session_id=session_id,
            config_id=config_id
        )
            
        result = momo_api.create_payment(
            order_id=momo_order_id,
            amount=int(amount),
            order_info=order_info,
            ipn_url=ipn_url
        )
        
        return result