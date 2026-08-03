# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install', 'trcf_inventory')
class TestDailyReport(HttpCase):
    """Regression test for trcf_report_controller.get_session_details():
    a closed pos.session whose config has no payment methods used to crash
    the whole /daily_report page with NameError('paid_orders' not defined),
    because paid_orders was only assigned inside `for pm in
    session.payment_method_ids:` and then read again after that loop.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = cls.env['res.users'].create({
            'name': 'TRCF Daily Report Test User',
            'login': 'trcf_daily_report_test_user',
            'password': 'trcf_daily_report_test_pwd_2026',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('point_of_sale.group_pos_user').id,
            ])],
        })

        # Config with zero payment methods - the trigger condition for the bug.
        cls.config = cls.env['pos.config'].create({
            'name': 'TRCF Test Config (no payment methods)',
            'payment_method_ids': [(5, 0, 0)],
        })
        now = datetime.now()
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.config.id,
            'user_id': cls.test_user.id,
            'start_at': now - timedelta(hours=2),
            'stop_at': now - timedelta(hours=1),
            'state': 'closed',
        })

        product = cls.env['product.product'].create({
            'name': 'TRCF Test Product (daily report)',
            'type': 'consu',
            'available_in_pos': True,
            'list_price': 30000,
        })
        cls.order = cls.env['pos.order'].create({
            'session_id': cls.pos_session.id,
            'company_id': cls.pos_session.company_id.id,
            'state': 'paid',
            'date_order': now - timedelta(hours=1, minutes=30),
            'amount_tax': 0,
            'amount_total': 30000,
            'amount_paid': 30000,
            'amount_return': 0,
            'lines': [(0, 0, {
                'product_id': product.id,
                'qty': 1,
                'price_unit': 30000,
                'price_subtotal': 30000,
                'price_subtotal_incl': 30000,
            })],
        })

    def test_daily_report_survives_session_with_no_payment_methods(self):
        self.authenticate('trcf_daily_report_test_user', 'trcf_daily_report_test_pwd_2026')
        response = self.url_open('/trcf_fnb_inventory/daily_report?filter_type=month')
        self.assertEqual(
            response.status_code, 200,
            "daily_report must not 500 when a closed session has no payment methods"
        )
