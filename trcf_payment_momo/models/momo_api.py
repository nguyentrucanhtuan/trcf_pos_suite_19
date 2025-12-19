import hashlib
import hmac
import json
import uuid
import requests
import logging

_logger = logging.getLogger(__name__)


class MoMoAPI:
    """
    MoMo Payment API Handler
    Handles signature generation and API calls to MoMo
    """
    
    # API Endpoints - theo tài liệu MoMo: https://developers.momo.vn/v3/docs/payment/api/wallet/onetime
    TEST_ENDPOINT = "https://test-payment.momo.vn/v2/gateway/api/create"
    PROD_ENDPOINT = "https://payment.momo.vn/v2/gateway/api/create"
    TEST_QUERY_ENDPOINT = "https://test-payment.momo.vn/v2/gateway/api/query"
    PROD_QUERY_ENDPOINT = "https://payment.momo.vn/v2/gateway/api/query"
    
    def __init__(self, partner_code, access_key, secret_key, test_mode=True):
        """
        Initialize MoMo API instance.
        
        Args:
            partner_code: MoMo Partner Code từ tài khoản M4B (bắt buộc)
            access_key: MoMo Access Key từ tài khoản M4B (bắt buộc)
            secret_key: MoMo Secret Key từ tài khoản M4B (bắt buộc)
            test_mode: True = sandbox, False = production
        
        Raises:
            ValueError: Nếu thiếu thông tin credentials
        """
        if not partner_code or not access_key or not secret_key:
            raise ValueError(
                "MoMo credentials chưa được cấu hình. "
                "Vui lòng vào POS > Payment Methods > MoMo để nhập Partner Code, Access Key và Secret Key."
            )
        
        self.partner_code = partner_code
        self.access_key = access_key
        self.secret_key = secret_key
        self.test_mode = test_mode
        self.endpoint = self.TEST_ENDPOINT if test_mode else self.PROD_ENDPOINT
        self.query_endpoint = self.TEST_QUERY_ENDPOINT if test_mode else self.PROD_QUERY_ENDPOINT
    
    def _generate_signature(self, raw_data):
        """
        Generate HMAC SHA256 signature
        """
        h = hmac.new(
            self.secret_key.encode('utf-8'),
            raw_data.encode('utf-8'),
            hashlib.sha256
        )
        return h.hexdigest()
    
    def create_payment(self, order_id, amount, order_info, redirect_url=None, ipn_url=None):
        """
        Create a MoMo payment request and get QR code URL
        
        Args:
            order_id: Unique order ID
            amount: Payment amount (integer, in VND)
            order_info: Order description
            redirect_url: URL to redirect after payment (optional for POS)
            ipn_url: Webhook URL for payment notification (optional)
            
        Returns:
            dict: {
                'success': bool,
                'qr_code_url': str,  # QR data to generate image
                'pay_url': str,      # URL for web payment
                'deeplink': str,     # MoMo app deeplink
                'message': str,
                'result_code': int
            }
        """
        request_id = str(uuid.uuid4())
        
        # Validate required URLs - theo MoMo API docs, ipnUrl là bắt buộc
        if not ipn_url:
            raise ValueError(
                "ipn_url là bắt buộc để nhận thông báo thanh toán từ MoMo. "
                "Vui lòng kiểm tra cấu hình web.base.url trong System Parameters."
            )
        
        # redirectUrl không cần thiết cho POS (không có web redirect), dùng ipn_url làm fallback
        if not redirect_url:
            redirect_url = ipn_url
        
        # Ensure amount is integer and > 0
        amount = int(amount)
        if amount < 1000:
            amount = 1000  # Minimum amount for MoMo
        
        # Build raw signature data - ORDER MATTERS! Must be alphabetical by key name
        # Based on MoMo documentation
        raw_signature = (
            f"accessKey={self.access_key}"
            f"&amount={amount}"
            f"&extraData="
            f"&ipnUrl={ipn_url}"
            f"&orderId={order_id}"
            f"&orderInfo={order_info}"
            f"&partnerCode={self.partner_code}"
            f"&redirectUrl={redirect_url}"
            f"&requestId={request_id}"
            f"&requestType=captureWallet"
        )
        
        signature = self._generate_signature(raw_signature)
        
        _logger.info(f"MoMo Signature raw: {raw_signature}")
        _logger.info(f"MoMo Signature: {signature}")
        
        # Build request payload
        payload = {
            "partnerCode": self.partner_code,
            "accessKey": self.access_key,
            "requestId": request_id,
            "amount": amount,
            "orderId": str(order_id),
            "orderInfo": order_info,
            "redirectUrl": redirect_url,
            "ipnUrl": ipn_url,
            "extraData": "",
            "requestType": "captureWallet",
            "signature": signature,
            "lang": "vi"
        }
        
        _logger.info(f"MoMo API Request: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            result = response.json()
            _logger.info(f"MoMo API Response: {json.dumps(result, indent=2)}")
            
            if result.get('resultCode') == 0:
                return {
                    'success': True,
                    'qr_code_url': result.get('qrCodeUrl', ''),
                    'pay_url': result.get('payUrl', ''),
                    'deeplink': result.get('deeplink', ''),
                    'message': result.get('message', 'Success'),
                    'result_code': 0,
                    'request_id': request_id
                }
            else:
                return {
                    'success': False,
                    'qr_code_url': '',
                    'pay_url': '',
                    'deeplink': '',
                    'message': result.get('message', 'Unknown error'),
                    'result_code': result.get('resultCode', -1),
                    'request_id': request_id
                }
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"MoMo API Error: {str(e)}")
            return {
                'success': False,
                'qr_code_url': '',
                'pay_url': '',
                'deeplink': '',
                'message': f"Connection error: {str(e)}",
                'result_code': -1,
                'request_id': request_id
            }
    
    def query_payment_status(self, order_id, request_id):
        """
        Query payment status from MoMo
        
        Args:
            order_id: Order ID used in create_payment
            request_id: Request ID from create_payment response
            
        Returns:
            dict: {
                'success': bool,
                'result_code': int,  # 0 = success, 1000 = pending, other = failed
                'message': str,
                'trans_id': str
            }
        """
        query_request_id = str(uuid.uuid4())
        
        # Build raw signature for query - theo MoMo docs
        raw_signature = (
            f"accessKey={self.access_key}"
            f"&orderId={order_id}"
            f"&partnerCode={self.partner_code}"
            f"&requestId={query_request_id}"
        )
        
        signature = self._generate_signature(raw_signature)
        
        payload = {
            "partnerCode": self.partner_code,
            "accessKey": self.access_key,
            "requestId": query_request_id,
            "orderId": str(order_id),
            "signature": signature,
            "lang": "vi"
        }
        
        _logger.info(f"MoMo Query Request: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(
                self.query_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            result = response.json()
            _logger.info(f"MoMo Query Response: {json.dumps(result, indent=2)}")
            
            return {
                'success': result.get('resultCode') == 0,
                'result_code': result.get('resultCode', -1),
                'message': result.get('message', ''),
                'trans_id': result.get('transId', ''),
                'amount': result.get('amount', 0)
            }
            
        except requests.exceptions.RequestException as e:
            _logger.error(f"MoMo Query Error: {str(e)}")
            return {
                'success': False,
                'result_code': -1,
                'message': f"Connection error: {str(e)}",
                'trans_id': ''
            }
