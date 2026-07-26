# -*- coding: utf-8 -*-
import json
import logging
import uuid

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

HD_GROUP = 'trcf_dl_pos_order.group_trcf_pos_hard_delete'

# Phiếu kho luôn được giữ lại (chỉ cắt liên kết pos_order_id) để không phá số
# liệu tồn kho / định giá đã hạch toán.
HD_KEEP_TABLES = ('stock_picking',)

# Số đơn tối đa cho một lần xoá, tránh transaction quá dài khoá bảng lâu.
HD_MAX_ORDERS_PER_RUN = 1000


class PosOrder(models.Model):
    _inherit = 'pos.order'

    # ------------------------------------------------------------------
    # Entry point từ giao diện
    # ------------------------------------------------------------------
    def action_trcf_hard_delete(self):
        """Mở wizard xác nhận xoá cứng cho các đơn đang chọn."""
        self._trcf_check_hard_delete_access()
        if not self:
            raise UserError(_("Hãy chọn ít nhất một đơn hàng để xoá."))
        if len(self) > HD_MAX_ORDERS_PER_RUN:
            raise UserError(_(
                "Chỉ xoá tối đa %(max)s đơn mỗi lần (đang chọn %(count)s đơn).",
                max=HD_MAX_ORDERS_PER_RUN, count=len(self),
            ))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Xoá cứng đơn hàng POS"),
            'res_model': 'trcf.pos.hard.delete.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_ids': self.ids},
        }

    def _trcf_check_hard_delete_access(self):
        if not self.env.user.has_group(HD_GROUP):
            raise AccessError(_(
                "Bạn không có quyền xoá cứng đơn hàng POS. Cần nhóm quyền "
                "'Xoá cứng đơn hàng POS'."
            ))

    # ------------------------------------------------------------------
    # Snapshot phục vụ nhật ký
    # ------------------------------------------------------------------
    def _trcf_hard_delete_snapshot(self):
        """Chụp lại dữ liệu đơn hàng trước khi xoá vĩnh viễn.

        Dùng sudo() vì người xoá có thể không có quyền đọc account.move /
        stock.picking, trong khi nhật ký bắt buộc phải ghi đủ thông tin đối soát.
        """
        snapshots = []
        for order in self.sudo():
            lines = [{
                'product': line.product_id.display_name,
                'qty': line.qty,
                'price_unit': line.price_unit,
                'discount': line.discount,
                'subtotal_incl': line.price_subtotal_incl,
            } for line in order.lines]
            payments = [{
                'method': payment.payment_method_id.display_name,
                'amount': payment.amount,
            } for payment in order.payment_ids]
            snapshots.append({
                'id': order.id,
                'name': order.name,
                'pos_reference': order.pos_reference,
                'date_order': fields.Datetime.to_string(order.date_order),
                'session': order.session_id.display_name,
                'config': order.config_id.display_name,
                'partner': order.partner_id.display_name,
                'amount_total': order.amount_total,
                'amount_paid': order.amount_paid,
                'state': order.state,
                'account_move_id': order.account_move.id,
                'account_move_name': order.account_move.name,
                'account_move_state': order.account_move.state,
                'picking_names': order.picking_ids.mapped('name'),
                'lines': lines,
                'payments': payments,
            })
        return snapshots

    def _trcf_hard_delete_preview(self, delete_account_move=True):
        """Chạy thử (dry-run) để biết những bảng nào sẽ bị đụng tới."""
        seeds = self._trcf_hard_delete_seeds(delete_account_move)
        plan, dummy = self.env['trcf.hard.delete.engine'].hd_run(
            seeds, keep_tables=HD_KEEP_TABLES, dry_run=True,
        )
        return plan

    def _trcf_hard_delete_seeds(self, delete_account_move):
        seeds = {'pos_order': set(self.ids)}
        if delete_account_move:
            # sudo(): người dùng POS thường không có quyền đọc account.move,
            # nhưng cần lấy id hoá đơn để đưa vào tập xoá.
            move_ids = set(self.sudo().mapped('account_move').ids)
            if move_ids:
                seeds['account_move'] = move_ids
        return seeds

    # ------------------------------------------------------------------
    # Thực thi
    # ------------------------------------------------------------------
    def _trcf_hard_delete(self, reason, delete_account_move=True):
        """Xoá vĩnh viễn các đơn hàng POS trong ``self``.

        Bỏ qua hoàn toàn tầng ORM (kể cả ``_unlink_except_draft_or_cancel``),
        thao tác trực tiếp trên Postgres và chấp nhận dữ liệu mồ côi ở những
        bảng chỉ tham chiếu lỏng.

        :return: dict đếm số dòng bị ảnh hưởng theo từng bảng.
        """
        self._trcf_check_hard_delete_access()
        if not reason or not reason.strip():
            raise UserError(_("Phải nhập lý do xoá."))

        snapshots = self._trcf_hard_delete_snapshot()
        seeds = self._trcf_hard_delete_seeds(delete_account_move)
        batch_uuid = uuid.uuid4().hex

        _logger.warning(
            "TRCF hard delete requested by uid=%s for pos.order %s (invoices=%s) reason=%r",
            self.env.uid, self.ids, sorted(seeds.get('account_move', ())), reason,
        )

        engine = self.env['trcf.hard.delete.engine']
        dummy, counters = engine.hd_run(seeds, keep_tables=HD_KEEP_TABLES)

        self._trcf_write_delete_logs(snapshots, counters, reason, batch_uuid,
                                     delete_account_move)
        return counters

    @api.model
    def _trcf_write_delete_logs(self, snapshots, counters, reason, batch_uuid,
                                delete_account_move):
        """Ghi nhật ký sau khi xoá.

        sudo(): nhóm xoá cứng chỉ có quyền đọc nhật ký, việc tạo bản ghi do hệ
        thống thực hiện để không ai sửa được dấu vết.
        """
        impact = json.dumps(
            {k: v for k, v in sorted(counters.items()) if v},
            ensure_ascii=False, indent=1,
        )
        self.env['trcf.pos.hard.delete.log'].sudo().create([{
            'order_ref': snap['name'] or _("(không tên)"),
            'deleted_order_id': snap['id'],
            'pos_reference': snap['pos_reference'],
            'date_order': snap['date_order'],
            'session_name': snap['session'],
            'config_name': snap['config'],
            'partner_name': snap['partner'],
            'amount_total': snap['amount_total'],
            'state_before': snap['state'],
            'account_move_name': snap['account_move_name'],
            'account_move_deleted': bool(delete_account_move and snap['account_move_id']),
            'picking_names': ', '.join(snap['picking_names']),
            'reason': reason,
            'user_id': self.env.uid,
            'batch_uuid': batch_uuid,
            'payload_json': json.dumps(snap, ensure_ascii=False, indent=1),
            'impact_json': impact,
        } for snap in snapshots])
