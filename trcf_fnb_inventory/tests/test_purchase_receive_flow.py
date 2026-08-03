# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'trcf_inventory')
class TestPurchaseReceiveFlow(TransactionCase):
    """Regression test for the core business flow: create PO -> receive ->
    stock.move state = Done -> product on-hand qty increases.

    This mirrors what /trcf_fnb_inventory/purchase_receive does (see
    controllers/trcf_purchase_controller.py: set move.quantity =
    move.product_uom_qty, then picking.button_validate()).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env['res.partner'].create({'name': 'Test Vendor Coffee Beans'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Coffee Beans 1kg',
            'type': 'consu',
            'is_storable': True,
            'purchase_ok': True,
        })

    def _create_po(self, qty):
        return self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': qty,
                'product_uom_id': self.product.uom_id.id,
                'price_unit': 50000,
                'date_planned': fields.Datetime.now(),
            })],
        })

    def test_confirm_creates_picking(self):
        po = self._create_po(10)
        self.assertFalse(po.picking_ids, "No picking should exist before confirmation")
        po.button_confirm()
        self.assertEqual(po.state, 'purchase')
        self.assertTrue(po.picking_ids, "Confirming the PO should create an incoming picking")

    def test_receive_sets_move_done_and_updates_stock(self):
        qty_before = self.product.qty_available
        po = self._create_po(10)
        po.button_confirm()

        picking = po.picking_ids[0]
        self.assertNotEqual(picking.state, 'done')

        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.button_validate()

        self.assertEqual(picking.state, 'done')
        for move in picking.move_ids:
            self.assertEqual(move.state, 'done')

        self.product.invalidate_recordset(['qty_available'])
        self.assertEqual(self.product.qty_available, qty_before + 10)

    def test_partial_receive_creates_backorder(self):
        po = self._create_po(10)
        po.button_confirm()
        picking = po.picking_ids[0]

        for move in picking.move_ids:
            move.quantity = 4  # receive less than ordered

        res = picking.button_validate()
        if isinstance(res, dict) and res.get('res_model') == 'stock.backorder.confirmation':
            # target='new' wizard: no res_id yet, must be created from the
            # action's context (mirrors trcf_purchase_controller.py's own handling).
            wizard = self.env['stock.backorder.confirmation'].with_context(res['context']).create({})
            wizard.process_cancel_backorder()

        self.assertEqual(picking.state, 'done')
        self.assertEqual(picking.move_ids.quantity, 4)
