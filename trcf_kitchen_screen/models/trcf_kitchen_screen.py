from odoo import api, fields, models

class TrcfKitchenScreen(models.Model):
    _name = 'trcf.kitchenscreen'
    _description = 'Kitchen Screen for Tuấn Rang Cà Phê'
    _rec_name = 'screen_name'

    screen_name = fields.Char(string='Tên màn hình', required=True)
    
    pos_config_id = fields.Many2one('pos.config', string='POS áp dụng', 
                                    help='Cấu hình POS sẽ hiển thị màn hình bếp này')
    
    pos_categ_ids = fields.Many2many('pos.category', string='Danh mục món hiển thị', 
                                     help='Chỉ những món thuộc danh mục này sẽ hiện lên bếp')
    
    is_active = fields.Boolean(string='Đang hoạt động', default=True)