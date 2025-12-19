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
        return super()._get_payment_terminal_selection() + [('trcf_momo', 'TRCF MOMO QR')]
    
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
        
        # Build API instance - credentials are required
        if not payment_method or not payment_method.momo_partner_code:
            return {
                'success': False,
                'qr_code_url': '',
                'pay_url': '',
                'deeplink': '',
                'message': 'MoMo chưa được cấu hình. Vui lòng vào POS > Payment Methods > MoMo để nhập Partner Code, Access Key và Secret Key.',
                'result_code': -1
            }
        
        try:
            momo_api = MoMoAPI(
                partner_code=payment_method.momo_partner_code,
                access_key=payment_method.momo_access_key,
                secret_key=payment_method.momo_secret_key,
                test_mode=payment_method.momo_test_mode
            )
        except ValueError as e:
            return {
                'success': False,
                'qr_code_url': '',
                'pay_url': '',
                'deeplink': '',
                'message': str(e),
                'result_code': -1
            }
        
        # Create payment
        if not order_info:
            order_info = f"Thanh toan don hang {momo_order_id}"
        
        # Store pending transaction for webhook matching
        Transaction = self.env['trcf.momo.transaction'].sudo()
        
        # Create payment first to get request_id
        result = momo_api.create_payment(
            order_id=momo_order_id,
            amount=int(amount),
            order_info=order_info,
            ipn_url=ipn_url
        )
        
        # Create transaction with request_id
        Transaction.create_pending_transaction(
            pos_order_ref=str(order_id),
            momo_order_id=momo_order_id,
            amount=float(amount),
            request_id=result.get('request_id'),
            session_id=session_id,
            config_id=config_id
        )
        
        # Add momo_order_id to result for polling
        if result.get('success'):
            result['momo_order_id'] = momo_order_id
        
        return result
    
    @api.model
    def check_momo_payment_status_rpc(self, momo_order_id):
        """
        RPC method to check MoMo payment status from POS
        
        Args:
            momo_order_id: MoMo order ID to check
            
        Returns:
            dict with success, status, result_code, message, trans_id
        """
        try:
            Transaction = self.env['trcf.momo.transaction'].sudo()
            transaction = Transaction.search([('momo_order_id', '=', momo_order_id)], limit=1)
            
            if not transaction:
                return {
                    'success': False,
                    'status': 'not_found',
                    'message': 'Transaction not found'
                }
            
            # If already success or failed, return cached status
            if transaction.status in ['success', 'failed']:
                return {
                    'success': transaction.status == 'success',
                    'status': transaction.status,
                    'result_code': transaction.result_code,
                    'message': transaction.message or '',
                    'trans_id': transaction.trans_id or ''
                }
            
            # Query MoMo API for current status
            payment_method = self.search([
                ('use_payment_terminal', '=', 'trcf_momo')
            ], limit=1)
            
            if not payment_method or not payment_method.momo_partner_code:
                return {
                    'success': False,
                    'status': 'error',
                    'message': 'MoMo not configured'
                }
            
            try:
                momo_api = MoMoAPI(
                    partner_code=payment_method.momo_partner_code,
                    access_key=payment_method.momo_access_key,
                    secret_key=payment_method.momo_secret_key,
                    test_mode=payment_method.momo_test_mode
                )
            except ValueError as e:
                return {
                    'success': False,
                    'status': 'error',
                    'message': str(e)
                }
            
            # Query payment status
            result = momo_api.query_payment_status(
                order_id=momo_order_id,
                request_id=transaction.momo_request_id or ''
            )
            
            # Update transaction if status changed
            if result['result_code'] == 0:  # Success
                transaction.write({
                    'status': 'success',
                    'result_code': result['result_code'],
                    'message': result['message'],
                    'trans_id': result['trans_id'],
                    'payment_time': fields.Datetime.now(),
                })
                # Send bus notification
                transaction._notify_pos_payment_success(transaction)
                
            elif result['result_code'] not in [1000, 9000]:  # Not pending
                transaction.write({
                    'status': 'failed',
                    'result_code': result['result_code'],
                    'message': result['message'],
                })
            
            return {
                'success': result['success'],
                'status': 'success' if result['success'] else ('pending' if result['result_code'] in [1000, 9000] else 'failed'),
                'result_code': result['result_code'],
                'message': result['message'],
                'trans_id': result.get('trans_id', '')
            }
            
        except Exception as e:
            _logger.error(f"Error checking MoMo payment status: {str(e)}")
            return {
                'success': False,
                'status': 'error',
                'message': str(e)
            }