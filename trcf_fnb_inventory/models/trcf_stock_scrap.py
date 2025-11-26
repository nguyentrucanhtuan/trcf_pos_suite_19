from odoo import models, fields, api


class TrcfStockScrap(models.Model):
    """
    Extend stock.scrap model to add custom description field for TRCF inventory management.
    Uses Odoo's built-in scrap_reason_id field for reason selection.
    """
    _inherit = 'stock.scrap'
    
    trcf_scrap_description = fields.Text(
        string='Mô tả chi tiết',
        help='Mô tả chi tiết về lý do hủy hàng hóa'
    )
