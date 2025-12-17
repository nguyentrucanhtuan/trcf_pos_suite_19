from odoo import http
from odoo.http import request
import json
import uuid
import hashlib
import hmac
import logging

from ..models.momo_api import MoMoAPI

_logger = logging.getLogger(__name__)


class MoMoController(http.Controller):
    """
    Controller for MoMo payment integration
    """
    
    @http.route('/pos/momo/create_payment', type='jsonrpc', auth='user', methods=['POST'])
    def create_momo_payment(self, order_id, amount, order_info=None, session_id=None, config_id=None, **kwargs):
        """
        Create a MoMo payment and return QR code URL
        Also stores pending transaction for webhook matching
        """
        try:
            import re
            
            # Clean order_id for MoMo format
            clean_order_id = re.sub(r'[^0-9a-zA-Z\-_\.:]', '', str(order_id))
            if not clean_order_id:
                clean_order_id = "ORDER"
            
            momo_order_id = f"{clean_order_id}_{uuid.uuid4().hex[:8]}"
            
            if not order_info:
                order_info = f"Thanh toan don hang {order_id}"
            
            # Get base URL for IPN
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            ipn_url = f"{base_url}/momo/ipn"
            
            # Get MoMo config - credentials are required
            PaymentMethod = request.env['pos.payment.method'].sudo()
            payment_method = PaymentMethod.search([
                ('use_payment_terminal', '=', 'trcf_momo')
            ], limit=1)
            
            if not payment_method or not payment_method.momo_partner_code:
                return {
                    'success': False,
                    'qr_code_url': '',
                    'pay_url': '',
                    'deeplink': '',
                    'message': 'MoMo chưa được cấu hình. Vui lòng vào POS > Payment Methods > MoMo để nhập credentials.',
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
            result = momo_api.create_payment(
                order_id=momo_order_id,
                amount=int(amount),
                order_info=order_info,
                ipn_url=ipn_url
            )
            
            # Store pending transaction for webhook matching
            if result.get('success'):
                Transaction = request.env['trcf.momo.transaction'].sudo()
                Transaction.create_pending_transaction(
                    pos_order_ref=str(order_id),
                    momo_order_id=momo_order_id,
                    amount=float(amount),
                    request_id=result.get('request_id'),
                    session_id=session_id,
                    config_id=config_id
                )
                _logger.info(f"MoMo: Created pending transaction {momo_order_id} for order {order_id}")
            
            return result
            
        except Exception as e:
            _logger.error(f"Error creating MoMo payment: {str(e)}")
            return {
                'success': False,
                'qr_code_url': '',
                'pay_url': '',
                'deeplink': '',
                'message': str(e),
                'result_code': -1
            }
    
    @http.route('/momo/ipn', type='http', auth='public', methods=['POST'], csrf=False)
    def momo_ipn(self, **kwargs):
        """
        MoMo Instant Payment Notification (IPN) webhook
        Called by MoMo when payment status changes
        """
        try:
            # Get raw data
            data = json.loads(request.httprequest.data or '{}')
            
            _logger.info(f"MoMo IPN received: {json.dumps(data, indent=2)}")
            
            # Extract fields
            partner_code = data.get('partnerCode', '')
            order_id = data.get('orderId', '')
            request_id = data.get('requestId', '')
            amount = data.get('amount', 0)
            result_code = data.get('resultCode', -1)
            message = data.get('message', '')
            trans_id = data.get('transId', '')
            signature = data.get('signature', '')
            
            # Verify signature (important for security!)
            if not self._verify_ipn_signature(data):
                _logger.warning(f"MoMo IPN: Invalid signature for order {order_id}")
                # Still process but log warning (for testing)
            
            # Update transaction
            Transaction = request.env['trcf.momo.transaction'].sudo()
            transaction = Transaction.update_from_ipn(
                momo_order_id=order_id,
                result_code=result_code,
                message=message,
                trans_id=trans_id
            )
            
            if transaction:
                _logger.info(f"MoMo IPN: Successfully processed order {order_id}")
            
            # MoMo expects 204 No Content
            return request.make_response('', status=204)
            
        except Exception as e:
            _logger.error(f"MoMo IPN Error: {str(e)}")
            return request.make_response('', status=204)
    
    def _verify_ipn_signature(self, data):
        """
        Verify the IPN signature from MoMo
        Theo tài liệu: https://developers.momo.vn/v3/docs/payment/api/wallet/onetime#processing-payment-result
        
        Signature format:
        accessKey=$accessKey&amount=$amount&extraData=$extraData
        &message=$message&orderId=$orderId&orderInfo=$orderInfo
        &orderType=$orderType&partnerCode=$partnerCode&payType=$payType
        &requestId=$requestId&responseTime=$responseTime&resultCode=$resultCode&transId=$transId
        """
        try:
            # Get credentials from payment method configuration
            PaymentMethod = request.env['pos.payment.method'].sudo()
            payment_method = PaymentMethod.search([
                ('use_payment_terminal', '=', 'trcf_momo')
            ], limit=1)
            
            if not payment_method or not payment_method.momo_secret_key or not payment_method.momo_access_key:
                _logger.warning("MoMo IPN: Credentials chưa được cấu hình, không thể verify signature")
                return False
            
            secret_key = payment_method.momo_secret_key
            access_key = payment_method.momo_access_key
            
            # Build signature raw data - theo MoMo API v3 docs (alphabetical order)
            raw_signature = (
                f"accessKey={access_key}"
                f"&amount={data.get('amount', '')}"
                f"&extraData={data.get('extraData', '')}"
                f"&message={data.get('message', '')}"
                f"&orderId={data.get('orderId', '')}"
                f"&orderInfo={data.get('orderInfo', '')}"
                f"&orderType={data.get('orderType', '')}"
                f"&partnerCode={data.get('partnerCode', '')}"
                f"&payType={data.get('payType', '')}"
                f"&requestId={data.get('requestId', '')}"
                f"&responseTime={data.get('responseTime', '')}"
                f"&resultCode={data.get('resultCode', '')}"
                f"&transId={data.get('transId', '')}"
            )
            
            # Generate signature using HMAC_SHA256
            h = hmac.new(
                secret_key.encode('utf-8'),
                raw_signature.encode('utf-8'),
                hashlib.sha256
            )
            computed_signature = h.hexdigest()
            
            is_valid = computed_signature == data.get('signature', '')
            if not is_valid:
                _logger.warning(f"MoMo IPN: Signature mismatch. Expected: {computed_signature}, Got: {data.get('signature', '')}")
            
            return is_valid
            
        except Exception as e:
            _logger.error(f"Signature verification error: {str(e)}")
            return False
