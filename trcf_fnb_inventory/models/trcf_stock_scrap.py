from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


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

    def do_scrap(self):
        """
        Override do_scrap to handle Kit products properly.
        For Kit products, we need to ensure the bom_id is set before processing.
        """
        for scrap in self:
            # Check if product is a Kit
            if scrap.product_id.is_kits:
                if not scrap.bom_id:
                    raise UserError(_('Sản phẩm "%s" là Kit. Vui lòng chọn BoM (công thức sản xuất) trước khi hủy.') % scrap.product_id.name)

                _logger.info(f"Processing scrap for Kit product {scrap.product_id.name} with BoM {scrap.bom_id.display_name}")

        # Call parent method
        return super(TrcfStockScrap, self).do_scrap()
