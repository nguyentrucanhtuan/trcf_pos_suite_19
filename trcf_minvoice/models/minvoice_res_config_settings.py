# -*- coding: utf-8 -*-
import requests
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class TrcfMInvoiceResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Thông tin MInvoice\
    minvoice_tax_code = fields.Char(
        string='Mã số thuế',
        config_parameter='trcf_minvoice.tax_code',
        help='Mã số thuế 10 hoặc 13 số'
    )
    
    minvoice_username = fields.Char(
        string='Username',
        config_parameter='trcf_minvoice.username'
    )
    
    minvoice_password = fields.Char(
        string='Password',
        config_parameter='trcf_minvoice.password'
    )

    minvoice_api_token = fields.Char(
        string='API Token Minvoice',
        config_parameter='trcf_minvoice.api_token',
        help='Token lấy từ Minvoice'
    )

    minvoice_api_token_display = fields.Char(
        string="MInvoice API Token (Hiển thị)",
        compute='_compute_minvoice_api_token_display'
    )

    minvoice_invoice_series = fields.Char(
        string='Ký hiệu hóa đơn',
        config_parameter='trcf_minvoice.invoice_series',
        help='Ví dụ: 1C25MYY'
    )

    minvoice_company_name = fields.Char(
        string='Tên cửa hàng/Công ty',
        config_parameter='trcf_minvoice.company_name',
        help='Tên đăng ký kinh doanh của cửa hàng'
    )

    def _compute_minvoice_api_token_display(self):
        for record in self:
            if record.minvoice_api_token and len(record.minvoice_api_token) > 15:
                record.minvoice_api_token_display = '...' + record.minvoice_api_token[-15:]
            else:
                record.minvoice_api_token_display = record.minvoice_api_token or ''

    def action_get_minvoice_token(self):
        
        for record in self:
            minvoice_username = record.minvoice_username
            minvoice_password = record.minvoice_password
            minvoice_tax_code = record.minvoice_tax_code

            url = f"https://{minvoice_tax_code}.minvoice.app/api/Account/Login"

            data = {
                "username": minvoice_username,
                "password": minvoice_password,
                "ma_dvcs": "VP"
            }

            try:
                # Gửi yêu cầu POST đến API Minvoice
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, json=data, headers=headers, timeout=10)
                
                # Kiểm tra trạng thái phản hồi
                response.raise_for_status()
                
                # Phân tích phản hồi JSON
                response_data = response.json()

                # Kiểm tra và lấy token
                if response_data and response_data.get('code') == "00":
                    token = response_data.get('token')

                    self.env['ir.config_parameter'].sudo().set_param('trcf_minvoice.api_token', token)

                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': '✅ Lấy token thành công',
                            'message': 'Đã lấy token thành công và lưu vào cấu hình vui lòng F5 trang',
                            'type': 'success',
                            'sticky': False,
                        }
                    }

                else:
                    _logger.error("API Minvoice trả về lỗi: %s", response_data.get('Message', 'Không có tin nhắn lỗi'))
                    return False

            except requests.exceptions.RequestException as e:
                _logger.error("Lỗi khi kết nối đến API Minvoice: %s", e)
                return False
            except Exception as e:
                _logger.error("Một lỗi không mong muốn đã xảy ra: %s", e)
                return False

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Lấy token thành công',
                'message': f'Đã lấy token thành công',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_get_minvoice_series(self): 

        for record in self:
            minvoice_tax_code = record.minvoice_tax_code
            minvoice_api_token = record.minvoice_api_token

            # Thông tin API
            url = f"https://{minvoice_tax_code}.minvoice.app/api/Invoice68/GetTypeInvoiceSeries"
            headers = {
                "Authorization": f"Bear {minvoice_api_token}"
            }

            try:
                # Thực hiện cuộc gọi API GET
                response = requests.get(url, headers=headers)

                # Kiểm tra mã trạng thái HTTP
                if response.status_code == 200:
                    # Chuyển đổi phản hồi JSON thành một đối tượng Python (dictionary)
                    data = response.json()

                    # Kiểm tra xem phản hồi có thành công không và có dữ liệu không
                    if data.get("ok") and data.get("code") == "00" and data.get("data"):
                        # Lấy giá trị "value" từ đối tượng đầu tiên trong mảng "data"
                        self.env['ir.config_parameter'].sudo().set_param('trcf_minvoice.invoice_series', data["data"][0]["value"])
                        
                        # Trả về kết quả thành công và ký hiệu hóa đơn
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': '✅ Lấy Minvoice Series thành công',
                                'message': f'Đã Lấy Minvoice Series: {data["data"][0]["value"]}. Vui lòng F5 trang',
                                'type': 'success',
                                'sticky': False,
                            }
                        }
                    else:
                        # Xử lý trường hợp API trả về lỗi hoặc không có dữ liệu
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': '❌ Lấy Minvoice Series thất bại',
                                'message': f'Lỗi từ API: {data.get("message", "Không rõ")}',
                                'type': 'danger',
                                'sticky': True,
                            }
                        }

                else:
                    # Xử lý các lỗi HTTP khác
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': '❌ Lỗi HTTP',
                            'message': f'Yêu cầu thất bại với mã trạng thái: {response.status_code}',
                            'type': 'danger',
                            'sticky': True,
                        }
                    }

            except requests.exceptions.RequestException as e:
                # Xử lý các lỗi mạng, kết nối
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '❌ Lỗi kết nối',
                        'message': f'Không thể kết nối tới Minvoice API: {e}',
                        'type': 'danger',
                        'sticky': True,
                    }
                }
        