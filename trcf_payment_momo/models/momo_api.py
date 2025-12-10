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
    
    # Test environment
    TEST_ENDPOINT = "https://test-payment.momo.vn/v2/gateway/api/create"
    PROD_ENDPOINT = "https://payment.momo.vn/v2/gateway/api/create"
    
    # Default test credentials (from MoMo official documentation)
    # https://developers.momo.vn/v2/#/docs/en/aio
    DEFAULT_PARTNER_CODE = "MOMO"
    DEFAULT_ACCESS_KEY = "F8BBA842ECF85"
    DEFAULT_SECRET_KEY = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
    
    def __init__(self, partner_code=None, access_key=None, secret_key=None, test_mode=True):
        self.partner_code = partner_code or self.DEFAULT_PARTNER_CODE
        self.access_key = access_key or self.DEFAULT_ACCESS_KEY
        self.secret_key = secret_key or self.DEFAULT_SECRET_KEY
        self.test_mode = test_mode
        self.endpoint = self.TEST_ENDPOINT if test_mode else self.PROD_ENDPOINT
    
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
        
        # Default URLs if not provided (required by MoMo API)
        if not redirect_url:
            redirect_url = "https://webhook.site/redirect"
        if not ipn_url:
            ipn_url = "https://webhook.site/ipn"
        
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
