from odoo import models, fields

class TrcfHrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    trcf_hourly_salary = fields.Float(
        string='Lương theo giờ',
        digits='Product Price',
        help='Mức lương theo giờ của nhân viên'
    )

    trcf_device_id_num = fields.Char(string='ZkTeco Device ID',
                                help="Id của nhân viên trên thiết bị")