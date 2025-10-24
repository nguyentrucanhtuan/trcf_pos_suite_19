# -*- coding: utf-8 -*-
from odoo import models, fields, api
import requests
import json

import logging

# KHAI BÁO LOGGER Ở ĐÂY
_logger = logging.getLogger(__name__)

class TrcfMinvoicePosOrder(models.Model):
    _inherit = 'pos.order'
    
    trcf_reference_tax_code = fields.Char(
        string='Mã Đối Chiếu VAT',
        copy=False,
        help='Mã đối chiếu để xác minh VAT cho đơn hàng'
    )
    
    trcf_is_vat_sent= fields.Boolean(
        string='Đã xuất VAT',
        compute='_compute_trcf_is_vat_sent',
        store=True,
        help='Đơn hàng chưa có mã đối chiếu VAT'
    )
    
    @api.depends('trcf_reference_tax_code')
    def _compute_trcf_is_vat_sent(self):
        for order in self:
            order.trcf_is_vat_sent = bool(order.trcf_reference_tax_code)


    def action_send_vat_minvoice_api(self):
        # Lấy danh sách pos_reference
        pos_references = self.mapped('pos_reference')

        # URL API
        API_URL = "https://0106026495-999.minvoice.app/api/InvoiceApi78/Save"
        API_TOKEN = "O87316arj5+Od3Fqyy5hzdBfIuPk73eKqpAzBSvv8sY=123"

        for order in self:
            # Dữ liệu mẫu theo format Minvoice
            payload = {
                "editmode": 1,
                "data": [
                    {
                        "inv_invoiceSeries": "1C25MYY",
                        "inv_invoiceIssuedDate": "2025-10-07",
                        "inv_currencyCode": "VND",
                        "inv_exchangeRate": 1,
                        "so_benh_an": order.pos_reference,
                        "inv_buyerDisplayName": "Nguyễn Văn A",
                        "inv_buyerLegalName": "CÔNG TY M-INVOICE",
                        "inv_buyerTaxCode": "0106026495-999",
                        "inv_buyerAddressLine": "Giáp Bát, Hoàng Mai, Hà Nội",
                        "inv_buyerEmail": "abc@gmail.com",
                        "inv_buyerBankAccount": "100003131",
                        "inv_buyerBankName": "Ngân hàng TMCP Á Châu - ACB",
                        "inv_paymentMethodName": "TM/CK",
                        "inv_discountAmount": 0,
                        "inv_TotalAmountWithoutVat": 610000,
                        "inv_vatAmount": 48800,
                        "inv_TotalAmount": 658800,
                        "key_api": order.pos_reference,
                        "cccdan": "034090008484",
                        "so_hchieu": "G1A2B3C4D",
                        "mdvqhnsach_nmua": "",
                        "ma_ch": "",
                        "ten_ch": "CÔNG TY TNHH TNT DRINK",
                        "details": [
                            {
                                "data": [
                                    {
                                        "tchat": 1,
                                        "stt_rec0": 1,
                                        "inv_itemCode": "HH001",
                                        "inv_itemName": "Hàng hóa 001",
                                        "inv_unitCode": "Phần",
                                        "inv_quantity": 1,
                                        "inv_unitPrice": 120000,
                                        "inv_discountPercentage": 0,
                                        "inv_discountAmount": 0,
                                        "inv_TotalAmountWithoutVat": 120000,
                                        "ma_thue": 8,
                                        "inv_vatAmount": 9600,
                                        "inv_TotalAmount": 129600
                                    },
                                    {
                                        "tchat": 1,
                                        "stt_rec0": 2,
                                        "inv_itemCode": "HH002",
                                        "inv_itemName": "Hàng hóa 002",
                                        "inv_unitCode": "Phần",
                                        "inv_quantity": 2,
                                        "inv_unitPrice": 245000,
                                        "inv_discountPercentage": 0,
                                        "inv_discountAmount": 0,
                                        "inv_TotalAmountWithoutVat": 490000,
                                        "ma_thue": 8,
                                        "inv_vatAmount": 39200,
                                        "inv_TotalAmount": 529200
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }

            try:
                # Headers
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {API_TOKEN}'
                }
                
                response = requests.post(
                    API_URL,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                # Kiểm tra status code
                response.raise_for_status()

                # Parse JSON response
                result = response.json()

                if result.get('ok') and result.get('code') == '00':
                    # Lấy sobaomat từ data
                    data = result.get('data', {})
                    sobaomat = data.get('sobaomat')
                    order.write({
                        'trcf_reference_tax_code': sobaomat,
                        'trcf_is_vat_sent': True,
                    })

                # Parse response JSON
                try:
                    _logger.info(f"📥 Parsed JSON Response:")
                    _logger.info(json.dumps(result, indent=2, ensure_ascii=False))
                except:
                    _logger.warning("⚠️  Response không phải JSON")
                    result = None
                
            except requests.exceptions.HTTPError as e:
                _logger.error(f"❌ HTTP Error: {e}")
                _logger.error(f"Response: {response.text if 'response' in locals() else 'N/A'}")
                
            except requests.exceptions.ConnectionError as e:
                _logger.error(f"❌ Connection Error: {e}")
                
            except requests.exceptions.Timeout as e:
                _logger.error(f"❌ Timeout Error: {e}")
                
            except Exception as e:
                _logger.error(f"❌ Unexpected Error: {e}")
                _logger.exception("Chi tiết lỗi:")
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Thành công',
                'message': f'Đã gửi dữ liệu lên Minvoice!\nStatus: Check terminal log để xem chi tiết response.',
                'type': 'success',
                'sticky': False,
            }
        }