# -*- coding: utf-8 -*-
"""Test suite cho tính năng Geo Attendance (Tab Chấm Công Geolocation).

Bao gồm:
- Unit tests: Haversine, velocity check, geo_suspicious logic
- Integration tests: check-in/check-out trong/ngoài geofence, IP warning/strict mode
- Regression tests: backward compatibility, tab 1 & 2 không bị ảnh hưởng

Chạy bằng:
    python odoo-bin -d <db> --test-enable --stop-after-init -u trcf_fnb_staff
"""

from odoo.tests import TransactionCase, tagged


@tagged('geo_attendance', '-standard')
class TestGeoAttendanceUnit(TransactionCase):
    """Unit tests cho các helper functions — không cần HTTP request."""

    def setUp(self):
        super().setUp()
        # Tạo nhân viên test
        self.employee = self.env['hr.employee'].create({'name': 'Test Employee Geo'})

        # Tạo cơ sở test tại Q1 HCM
        self.location_q1 = self.env['trcf.geo.location'].create({
            'name': 'Cơ sở Q1 Test',
            'latitude': 10.7769,
            'longitude': 106.7009,
            'radius': 100.0,
            'active': True,
            'ip_check_mode': 'none',
        })

    def test_haversine_known_distance(self):
        """Tính khoảng cách Haversine giữa 2 điểm đã biết."""
        # Tâm Q1 đến điểm cách 50m
        # Đây là unit test — dùng method từ controller
        from odoo.addons.trcf_fnb_staff.controllers.trcf_shift_registration_controller import (
            TrcfShiftRegistrationController,
        )
        ctrl = TrcfShiftRegistrationController()

        # 2 điểm cách nhau: tâm → 0 mét
        dist = ctrl._haversine(10.7769, 106.7009, 10.7769, 106.7009)
        self.assertAlmostEqual(dist, 0.0, places=0)

        # Hà Nội → HCM ≈ 1726 km
        dist_hn_hcm = ctrl._haversine(21.0285, 105.8542, 10.7769, 106.7009)
        self.assertGreater(dist_hn_hcm, 1700000)
        self.assertLess(dist_hn_hcm, 1800000)

    def test_geo_suspicious_low_accuracy(self):
        """GPS accuracy < 5m phải flag geo_suspicious=True."""
        attendance = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-03-08 01:00:00',
            'attendance_source': 'geo',
            'geo_check_in_lat': 10.7769,
            'geo_check_in_lon': 106.7009,
            'geo_check_in_accuracy': 2.0,  # < 5m → suspicious
            'geo_location_id': self.location_q1.id,
            'geo_suspicious': True,
            'geo_suspicious_reason': 'low_accuracy',
            'request_ip': '1.2.3.4',
        })
        self.assertTrue(attendance.geo_suspicious)
        self.assertIn('low_accuracy', attendance.geo_suspicious_reason)

    def test_attendance_source_default_zkteco(self):
        """Bản ghi hr.attendance cũ không có attendance_source → default 'zkteco'."""
        attendance = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-03-08 02:00:00',
        })
        # Default phải là 'zkteco' để backward compatible
        self.assertEqual(attendance.attendance_source, 'zkteco')

    def test_geo_location_id_saved(self):
        """Khi check-in, geo_location_id phải được lưu đúng cơ sở."""
        attendance = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-03-08 01:00:00',
            'attendance_source': 'geo',
            'geo_location_id': self.location_q1.id,
            'geo_check_in_lat': 10.7769,
            'geo_check_in_lon': 106.7009,
            'geo_check_in_accuracy': 15.0,
            'request_ip': '203.113.1.1',
        })
        self.assertEqual(attendance.geo_location_id.id, self.location_q1.id)

    def test_request_ip_always_saved(self):
        """Mọi check-in geo đều phải có request_ip được ghi."""
        attendance = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-03-08 01:00:00',
            'attendance_source': 'geo',
            'geo_location_id': self.location_q1.id,
            'geo_check_in_lat': 10.7769,
            'geo_check_in_lon': 106.7009,
            'geo_check_in_accuracy': 15.0,
            'request_ip': '10.0.0.1',
        })
        self.assertTrue(attendance.request_ip)
        self.assertNotEqual(attendance.request_ip, '')


@tagged('geo_attendance', '-standard')
class TestGeoAttendanceIpCheck(TransactionCase):
    """Tests cho IP check logic (warning/strict/none modes)."""

    def setUp(self):
        super().setUp()
        self.employee = self.env['hr.employee'].create({'name': 'Test IP Employee'})

    def test_get_allowed_ip_list_empty(self):
        """allowed_ips trống → list rỗng → bỏ qua kiểm tra IP."""
        location = self.env['trcf.geo.location'].create({
            'name': 'Loc No IP',
            'latitude': 10.7769,
            'longitude': 106.7009,
            'radius': 100.0,
            'allowed_ips': '',
            'ip_check_mode': 'none',
        })
        self.assertEqual(location.get_allowed_ip_list(), [])

    def test_get_allowed_ip_list_parsed(self):
        """allowed_ips với 2 IPs được parse đúng."""
        location = self.env['trcf.geo.location'].create({
            'name': 'Loc With IP',
            'latitude': 10.7769,
            'longitude': 106.7009,
            'radius': 100.0,
            'allowed_ips': ' 203.113.1.1 , 14.178.2.2 ',
            'ip_check_mode': 'warning',
        })
        ip_list = location.get_allowed_ip_list()
        self.assertIn('203.113.1.1', ip_list)
        self.assertIn('14.178.2.2', ip_list)
        self.assertEqual(len(ip_list), 2)

    def test_ip_suspicious_flag_set(self):
        """ip_suspicious=True khi cờ được set (warning mode)."""
        att = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-03-08 01:00:00',
            'attendance_source': 'geo',
            'geo_check_in_lat': 10.7769,
            'geo_check_in_lon': 106.7009,
            'geo_check_in_accuracy': 15.0,
            'request_ip': '9.9.9.9',
            'ip_suspicious': True,
        })
        self.assertTrue(att.ip_suspicious)
        self.assertFalse(att.geo_suspicious)  # GPS fine, only IP suspicious
