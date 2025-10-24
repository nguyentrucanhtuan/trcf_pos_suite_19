from odoo import models, fields, api


class TrcfHrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # Field related - không lưu trữ, chỉ hiển thị
    trcf_hourly_salary_display = fields.Float(
        string='Tiền lương/giờ',
        related='employee_id.trcf_hourly_salary',
        digits='Product Price',
        help='Mức lương theo giờ của nhân viên',
        readonly=True,
        aggregator='max'  # Hoặc 'min', 'avg' - sẽ lấy giá trị thay vì sum
    )
    
    trcf_hourly_salary_sum = fields.Float(
        string='Tiền lương',
        digits='Product Price',
        help='Tiền lương cho phiên làm việc này',
        default=0.0,
        compute='_compute_hourly_salary_sum',
        store=True
    )

    @api.depends('worked_hours', 'employee_id.trcf_hourly_salary')
    def _compute_hourly_salary_sum(self):
        """Tính tiền lương = lương theo giờ * số giờ làm việc"""
        for record in self:
            if record.worked_hours and record.employee_id.trcf_hourly_salary:
                record.trcf_hourly_salary_sum = record.worked_hours * record.employee_id.trcf_hourly_salary
            else:
                record.trcf_hourly_salary_sum = 0.0