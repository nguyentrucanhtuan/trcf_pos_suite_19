# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _


class TrcfGeoLocation(models.Model):
    """Cấu hình vùng geofence cho từng cơ sở/chi nhánh dùng cho chấm công Geolocation.

    Mỗi cơ sở có tọa độ GPS trung tâm (latitude, longitude) và bán kính (radius).
    Ngoài ra có thể cấu hình danh sách public IP WiFi văn phòng để xác minh thiết bị.
    """

    _name = 'trcf.geo.location'
    _description = 'Vị trí Geofence Chấm Công'
    _order = 'name'

    name = fields.Char(
        string='Tên cơ sở',
        required=True,
        help='Tên cơ sở hoặc chi nhánh'
    )

    latitude = fields.Float(
        string='Vĩ độ (Latitude)',
        required=True,
        default=0.0,
        digits=(10, 7),
        help='Vĩ độ tâm geofence (decimal degrees, ví dụ: 10.7769)'
    )

    longitude = fields.Float(
        string='Kinh độ (Longitude)',
        required=True,
        default=0.0,
        digits=(10, 7),
        help='Kinh độ tâm geofence (decimal degrees, ví dụ: 106.7009)'
    )

    radius = fields.Float(
        string='Bán kính (mét)',
        required=True,
        default=100.0,
        help='Bán kính vùng cho phép chấm công tính từ tâm (mét)'
    )

    active = fields.Boolean(
        string='Đang hoạt động',
        default=True,
        help='Tắt để ẩn cơ sở này khỏi danh sách kiểm tra vị trí'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Công ty',
        default=lambda self: self.env.company,
        help='Công ty sở hữu cơ sở này (multi-company)'
    )

    description = fields.Text(
        string='Ghi chú',
        help='Mô tả thêm về cơ sở'
    )

    allowed_ips = fields.Text(
        string='Danh sách IP WiFi văn phòng',
        help=(
            'Danh sách public IP của đường truyền WiFi văn phòng, cách nhau bởi dấu phẩy. '
            'Ví dụ: 203.113.1.1, 14.178.2.2. '
            'Để trống để bỏ qua kiểm tra IP.'
        )
    )

    ip_check_mode = fields.Selection(
        selection=[
            ('none', 'Không kiểm tra'),
            ('warning', 'Cảnh báo (ghi flag nhưng cho check-in)'),
            ('strict', 'Bắt buộc (từ chối nếu IP không hợp lệ)'),
        ],
        string='Chế độ kiểm tra IP',
        default='none',
        required=True,
        help=(
            'none: bỏ qua kiểm tra IP; '
            'warning: ghi flag ip_suspicious nhưng vẫn cho check-in; '
            'strict: từ chối check-in nếu IP không thuộc danh sách allowed_ips'
        )
    )

    # ===== CONSTRAINTS =====

    _sql_constraints = [
        ('radius_positive', 'CHECK(radius > 0)', 'Bán kính phải lớn hơn 0 mét'),
        ('latitude_range', 'CHECK(latitude BETWEEN -90 AND 90)', 'Vĩ độ phải trong khoảng -90 đến 90'),
        ('longitude_range', 'CHECK(longitude BETWEEN -180 AND 180)', 'Kinh độ phải trong khoảng -180 đến 180'),
    ]

    def get_allowed_ip_list(self):
        """Trả về danh sách IP được phép dạng list[str], bỏ khoảng trắng.

        Returns:
            list[str]: Danh sách IP strings. Trả về [] nếu allowed_ips trống.
        """
        self.ensure_one()
        if not self.allowed_ips:
            return []
        return [ip.strip() for ip in self.allowed_ips.split(',') if ip.strip()]
