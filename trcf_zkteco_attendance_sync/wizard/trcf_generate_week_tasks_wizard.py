# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta


class TrcfGenerateWeekTasksWizard(models.TransientModel):
    _name = 'trcf.generate.week.tasks.wizard'
    _description = 'Wizard tạo công việc tuần'

    start_date = fields.Date(
        string='Ngày bắt đầu tuần (Thứ 2)',
        required=True,
        default=lambda self: self._default_start_date()
    )
    
    end_date = fields.Date(
        string='Ngày kết thúc (Chủ nhật)',
        compute='_compute_end_date'
    )

    def _default_start_date(self):
        """Mặc định: Thứ 2 tuần tiếp theo"""
        today = fields.Date.today()
        days_until_next_monday = (7 - today.weekday()) % 7
        if days_until_next_monday == 0:
            days_until_next_monday = 7
        return today + timedelta(days=days_until_next_monday)

    @api.depends('start_date')
    def _compute_end_date(self):
        for rec in self:
            if rec.start_date:
                rec.end_date = rec.start_date + timedelta(days=6)
            else:
                rec.end_date = False

    def action_generate(self):
        """Tạo công việc cho tuần đã chọn"""
        self.ensure_one()
        
        Template = self.env['trcf.shift.task.template']
        created_tasks = Template.action_generate_week_tasks(self.start_date)
        
        # Hiển thị danh sách tasks đã tạo
        return {
            'name': f'Công việc tuần {self.start_date} - {self.end_date}',
            'type': 'ir.actions.act_window',
            'res_model': 'trcf.shift.task',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created_tasks.ids)],
            'context': {'search_default_group_date': 1},
        }
