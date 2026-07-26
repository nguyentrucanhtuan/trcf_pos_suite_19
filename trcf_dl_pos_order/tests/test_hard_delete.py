# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged('post_install', '-at_install', 'trcf_dl_pos_order')
class TestTrcfHardDeletePosOrder(TestPoSCommon):

    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.product100 = self.create_product('Product_100', self.categ_basic, 100, 50)
        self.hd_group = self.env.ref('trcf_dl_pos_order.group_trcf_pos_hard_delete')
        self.env.user.group_ids |= self.hd_group

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _make_order(self, is_invoiced=False, uuid='hd-0001'):
        self.open_new_session()
        orders = self._create_orders([{
            'pos_order_lines_ui_args': [(self.product100, 1)],
            'payments': [(self.cash_pm1, 100)],
            'customer': self.customer,
            'is_invoiced': is_invoiced,
            'uuid': uuid,
        }])
        return orders[uuid]

    def _row_count(self, table, column, value):
        self.env.cr.execute(
            'SELECT COUNT(*) FROM "%s" WHERE "%s" = %%s' % (table, column), (value,)
        )
        return self.env.cr.fetchone()[0]

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------
    def test_delete_paid_order_removes_lines_and_payments(self):
        """Đơn đã thanh toán bị ORM chặn nhưng phải xoá cứng được."""
        order = self._make_order()
        order_id = order.id
        self.assertEqual(order.state, 'paid')
        with self.assertRaises(UserError):
            order.unlink()

        order._trcf_hard_delete(reason="test paid order")

        self.assertFalse(self.env['pos.order'].search([('id', '=', order_id)]))
        self.assertEqual(self._row_count('pos_order_line', 'order_id', order_id), 0)
        self.assertEqual(self._row_count('pos_payment', 'pos_order_id', order_id), 0)

    def test_delete_invoiced_order_removes_account_move(self):
        """Tuỳ chọn xoá hoá đơn phải xoá cả bút toán đã vào sổ và các dòng của nó."""
        order = self._make_order(is_invoiced=True, uuid='hd-0002')
        move = order.account_move
        self.assertTrue(move, "Đơn phải có hoá đơn để kiểm tra.")
        self.assertEqual(move.state, 'posted')
        move_id = move.id

        order._trcf_hard_delete(reason="test invoiced", delete_account_move=True)

        self.assertFalse(self.env['account.move'].search([('id', '=', move_id)]))
        self.assertEqual(self._row_count('account_move_line', 'move_id', move_id), 0)
        self.assertEqual(
            self._row_count('account_partial_reconcile', 'exchange_move_id', move_id), 0,
        )

    def test_keep_account_move_when_option_off(self):
        """Bỏ chọn xoá hoá đơn thì bút toán phải còn nguyên."""
        order = self._make_order(is_invoiced=True, uuid='hd-0003')
        move_id = order.account_move.id

        order._trcf_hard_delete(reason="keep move", delete_account_move=False)

        move = self.env['account.move'].browse(move_id)
        self.assertTrue(move.exists())
        self.assertEqual(move.state, 'posted')

    def test_stock_picking_is_kept_and_orphaned(self):
        """Phiếu kho phải được giữ lại, chỉ mất tham chiếu tới đơn POS."""
        order = self._make_order(uuid='hd-0004')
        pickings = order.picking_ids
        if not pickings:
            self.skipTest("Cấu hình POS không tạo phiếu kho.")
        picking_ids = pickings.ids

        order._trcf_hard_delete(reason="keep picking")

        remaining = self.env['stock.picking'].browse(picking_ids)
        self.assertTrue(all(remaining.mapped(lambda p: p.exists())))
        self.assertFalse(any(remaining.mapped('pos_order_id')))

    def test_log_is_written(self):
        order = self._make_order(uuid='hd-0005')
        order_name, order_id = order.name, order.id

        order._trcf_hard_delete(reason="lý do kiểm thử")

        log = self.env['trcf.pos.hard.delete.log'].search([
            ('deleted_order_id', '=', order_id),
        ])
        self.assertEqual(len(log), 1)
        self.assertEqual(log.order_ref, order_name)
        self.assertEqual(log.reason, "lý do kiểm thử")
        self.assertTrue(log.payload_json)
        self.assertTrue(log.impact_json)

    def test_access_denied_without_group(self):
        order = self._make_order(uuid='hd-0006')
        self.env.user.group_ids -= self.hd_group
        with self.assertRaises(AccessError):
            order._trcf_hard_delete(reason="no rights")

    def test_wizard_requires_confirm_keyword(self):
        order = self._make_order(uuid='hd-0007')
        wizard = self.env['trcf.pos.hard.delete.wizard'].create({
            'order_ids': [(6, 0, order.ids)],
            'reason': "test",
            'confirm_text': "xoa nham",
        })
        with self.assertRaises(UserError):
            wizard.action_hard_delete()
        self.assertTrue(order.exists())

        wizard.confirm_text = 'xoa'  # không phân biệt hoa thường
        wizard.action_hard_delete()
        self.assertFalse(self.env['pos.order'].search([('id', '=', order.id)]))

    def test_wizard_preview_lists_pos_tables(self):
        order = self._make_order(uuid='hd-0008')
        plan = order._trcf_hard_delete_preview(delete_account_move=True)
        tables = {table for table, dummy_depth, dummy_ids in plan['delete']}
        self.assertIn('pos_order', tables)
        self.assertIn('pos_order_line', tables)
        self.assertIn('pos_payment', tables)
        nullified = {'%s.%s' % (src, col) for src, col, dummy in plan['nullify']}
        self.assertIn('stock_picking.pos_order_id', nullified)

    def test_engine_never_deletes_master_tables(self):
        order = self._make_order(uuid='hd-0009')
        plan = order._trcf_hard_delete_preview(delete_account_move=True)
        tables = {table for table, dummy_depth, dummy_ids in plan['delete']}
        for protected in ('res_partner', 'res_company', 'product_product',
                          'account_journal', 'pos_session', 'stock_picking'):
            self.assertNotIn(protected, tables)
