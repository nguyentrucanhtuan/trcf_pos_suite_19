# -*- coding: utf-8 -*-
from odoo.tests import HttpCase, tagged

# GET-able pages served by trcf_fnb_inventory's controllers. Every one of
# them includes the shared sidebar (trcf_sidebar_template.xml), which is
# enough on its own to prove the page rendered and that the t() translation
# layer is wired into that controller's render() context (this is exactly
# what previously broke QWeb with a "t is undefined" error, per the module's
# controllers all needing `'t': get_translator(request)` in their vals).
ROUTES = [
    '/trcf_fnb_inventory/dashboard',
    '/trcf_fnb_inventory/purchase_list',
    '/trcf_fnb_inventory/purchase_add',
    '/trcf_fnb_inventory/scrap_list',
    '/trcf_fnb_inventory/scrap_add',
    '/trcf_fnb_inventory/transfer_list',
    '/trcf_fnb_inventory/transfer_add',
    '/trcf_fnb_inventory/processing_list',
    '/trcf_fnb_inventory/processing_add',
    '/trcf_fnb_inventory/expense_list',
    '/trcf_fnb_inventory/expense_add',
    '/trcf_fnb_inventory/check_inventory_list',
    '/trcf_fnb_inventory/check_inventory_add',
    '/trcf_fnb_inventory/daily_report',
    '/trcf_fnb_inventory/move_report',
]

# Sidebar nav label that's present on every page, in each language
# (extra-addons/trcf_pos_suite_19/trcf_fnb_inventory/views/trcf_sidebar_template.xml).
SIDEBAR_MARKER = {
    'vi_VN': 'TỔNG QUAN',
    'en_US': 'OVERVIEW',
}


@tagged('post_install', '-at_install', 'trcf_inventory')
class TestHttpSmoke(HttpCase):
    """Curl-equivalent smoke test: hit every trcf_fnb_inventory page while
    authenticated, in both languages, and assert 200 + the sidebar renders
    in the expected language. Uses a throwaway user created inside the
    test transaction (rolled back after the test run) instead of real
    login credentials."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Groups needed to match a real staff member using this app: base
        # internal user + stock/purchase/POS/MRP "User" (daily_report reads
        # pos.order, which needs at least Inventory or POS user access).
        group_xmlids = [
            'base.group_user',
            'stock.group_stock_user',
            'purchase.group_purchase_user',
            'point_of_sale.group_pos_user',
            'mrp.group_mrp_user',
        ]
        group_ids = [cls.env.ref(xmlid).id for xmlid in group_xmlids]
        cls.test_user = cls.env['res.users'].create({
            'name': 'TRCF Smoke Test User',
            'login': 'trcf_smoke_test_user',
            'password': 'trcf_smoke_test_pwd_2026',
            'group_ids': [(6, 0, group_ids)],
        })

    def _check_routes_in_lang(self, lang, marker):
        self.test_user.write({'lang': lang})
        for route in ROUTES:
            with self.subTest(route=route, lang=lang):
                response = self.url_open(route)
                self.assertEqual(
                    response.status_code, 200,
                    f"{route} returned {response.status_code} (lang={lang})"
                )
                body = response.text
                self.assertIn(
                    marker, body,
                    f"{route} did not render the expected '{lang}' sidebar marker "
                    f"'{marker}' — page may not have received 't' in its render context"
                )

    def test_all_pages_render_in_vietnamese(self):
        self.authenticate('trcf_smoke_test_user', 'trcf_smoke_test_pwd_2026')
        self._check_routes_in_lang('vi_VN', SIDEBAR_MARKER['vi_VN'])

    def test_all_pages_render_in_english(self):
        self.authenticate('trcf_smoke_test_user', 'trcf_smoke_test_pwd_2026')
        self._check_routes_in_lang('en_US', SIDEBAR_MARKER['en_US'])
