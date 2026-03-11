# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta
import pytz

class TrcfShiftConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    trcf_auto_generate_weekly_tasks = fields.Boolean(
        string='Tự động tạo công việc tuần',
        config_parameter='trcf_fnb_staff.trcf_auto_generate_weekly_tasks',
        help='Nếu bật, hệ thống sẽ tự động tạo danh sách công việc cho tuần kế tiếp.'
    )

    trcf_weekly_tasks_day = fields.Selection([
        ('0', 'Thứ 2'),
        ('1', 'Thứ 3'),
        ('2', 'Thứ 4'),
        ('3', 'Thứ 5'),
        ('4', 'Thứ 6'),
        ('5', 'Thứ 7'),
        ('6', 'Chủ nhật'),
    ], string='Ngày chạy hàng tuần', 
       config_parameter='trcf_fnb_staff.trcf_weekly_tasks_day',
       default='6',
       help='Chọn ngày trong tuần để tự động tạo công việc cho tuần sau.')

    trcf_weekly_tasks_time = fields.Float(
        string='Giờ chạy',
        config_parameter='trcf_fnb_staff.trcf_weekly_tasks_time',
        default=23.0,
        help='Chọn giờ trong ngày để chạy tác vụ tự động (tính theo giờ địa phương).')

    @api.model
    def get_values(self):
        res = super(TrcfShiftConfigSettings, self).get_values()
        # Lấy thêm giá trị nếu config_parameter không tự động handle (thường nó handle tốt cho Boolean và Char/Selection)
        return res

    def set_values(self):
        super(TrcfShiftConfigSettings, self).set_values()
        
        # Cập nhật Cron Job
        cron = self.env.ref('trcf_fnb_staff.trcf_cron_generate_weekly_tasks', raise_if_not_found=False)
        if cron:
            cron.sudo().write({
                'active': self.trcf_auto_generate_weekly_tasks,
            })
            
            if self.trcf_auto_generate_weekly_tasks:
                self._update_cron_nextcall(cron)

    def _update_cron_nextcall(self, cron):
        """Tính toán nextcall dựa trên ngày và giờ cấu hình (theo timezone local)"""
        user_tz = self.env.user.tz or 'Asia/Saigon'
        tz = pytz.timezone(user_tz)
        now_local = datetime.now(tz)
        
        target_day = int(self.trcf_weekly_tasks_day)
        target_hour = int(self.trcf_weekly_tasks_time)
        target_minute = int((self.trcf_weekly_tasks_time - target_hour) * 60)
        
        # Tạo datetime cho lần chạy tiếp theo ở local
        next_call_local = now_local.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        # Tính toán để tìm ngày tiếp theo có target_day
        days_ahead = target_day - next_call_local.weekday()
        if days_ahead < 0 or (days_ahead == 0 and next_call_local <= now_local):
            days_ahead += 7
            
        next_call_local += timedelta(days=days_ahead)
        
        # Chuyển về UTC để lưu vào Odoo
        next_call_utc = next_call_local.astimezone(pytz.utc).replace(tzinfo=None)
        
        cron.sudo().write({
            'nextcall': next_call_utc,
            'interval_number': 1,
            'interval_type': 'weeks',
        })
