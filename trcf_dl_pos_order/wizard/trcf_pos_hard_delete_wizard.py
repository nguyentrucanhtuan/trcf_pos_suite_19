# -*- coding: utf-8 -*-
from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Người dùng phải gõ đúng chuỗi này mới được xoá.
HD_CONFIRM_KEYWORD = 'XOA'

# Trạng thái đơn được coi là "đã chốt", xoá sẽ làm lệch số liệu.
HD_SENSITIVE_STATES = ('paid', 'done', 'invoiced')


class TrcfPosHardDeleteWizard(models.TransientModel):
    _name = 'trcf.pos.hard.delete.wizard'
    _description = 'Xác nhận xoá cứng đơn hàng POS'

    order_ids = fields.Many2many('pos.order', string="Đơn hàng", required=True)
    order_count = fields.Integer(string="Số đơn", compute='_compute_summary')
    amount_total = fields.Float(string="Tổng tiền", compute='_compute_summary',
                                digits=(16, 2))
    currency_id = fields.Many2one('res.currency', compute='_compute_summary')

    delete_account_move = fields.Boolean(
        string="Xoá luôn hoá đơn / bút toán kế toán", default=True,
        help="Bỏ chọn nếu chỉ muốn cắt liên kết và giữ lại bút toán kế toán.",
    )

    order_html = fields.Html(string="Danh sách đơn", compute='_compute_order_html',
                             sanitize=False)
    warning_html = fields.Html(string="Cảnh báo", compute='_compute_warning_html',
                               sanitize=False)
    impact_html = fields.Html(string="Bảng tác động", compute='_compute_impact_html',
                              sanitize=False)

    reason = fields.Text(string="Lý do xoá", required=True)
    confirm_text = fields.Char(
        string="Gõ để xác nhận", required=True,
        help="Gõ chính xác %s (in hoa, không dấu) để bật nút xoá." % HD_CONFIRM_KEYWORD,
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends('order_ids')
    def _compute_summary(self):
        for wizard in self:
            orders = wizard.order_ids
            wizard.order_count = len(orders)
            wizard.amount_total = sum(orders.mapped('amount_total'))
            wizard.currency_id = orders[:1].currency_id or self.env.company.currency_id

    @api.depends('order_ids')
    def _compute_order_html(self):
        for wizard in self:
            orders = wizard.order_ids
            if not orders:
                wizard.order_html = Markup('<p class="text-muted">%s</p>') % _(
                    "Chưa chọn đơn hàng nào."
                )
                continue
            header = Markup(
                '<table class="table table-sm o_list_table">'
                '<thead><tr>'
                '<th>%s</th><th>%s</th><th>%s</th><th>%s</th>'
                '<th class="text-end">%s</th><th>%s</th>'
                '</tr></thead><tbody>'
            ) % (_("Số đơn"), _("Ngày"), _("Phiên"), _("Trạng thái"),
                 _("Tổng tiền"), _("Hoá đơn"))
            rows = Markup('').join(
                Markup(
                    '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
                    '<td class="text-end">%s</td><td>%s</td></tr>'
                ) % (
                    escape(order.name or ''),
                    escape(fields.Datetime.to_string(order.date_order) or ''),
                    escape(order.session_id.display_name or ''),
                    escape(order.state or ''),
                    escape('{:,.0f}'.format(order.amount_total)),
                    escape(order.sudo().account_move.name or '-'),
                )
                for order in orders[:200]
            )
            footer = Markup('</tbody></table>')
            if len(orders) > 200:
                footer += Markup('<p class="text-muted">%s</p>') % _(
                    "... và %s đơn khác.", len(orders) - 200,
                )
            wizard.order_html = header + rows + footer

    @api.depends('order_ids', 'delete_account_move')
    def _compute_warning_html(self):
        for wizard in self:
            # sudo(): cần đọc account.move và pos.session để cảnh báo, người
            # dùng POS có thể không có quyền đọc các model này.
            orders = wizard.order_ids.sudo()
            messages = []

            sensitive = orders.filtered(lambda o: o.state in HD_SENSITIVE_STATES)
            if sensitive:
                messages.append(_(
                    "%s đơn ở trạng thái đã chốt (paid/done/invoiced): doanh thu, "
                    "báo cáo phiên và sổ quỹ sẽ lệch sau khi xoá.", len(sensitive),
                ))

            open_sessions = orders.session_id.filtered(lambda s: s.state != 'closed')
            if open_sessions:
                messages.append(_(
                    "Các phiên chưa đóng sẽ bị lệch số liệu: %s",
                    ', '.join(open_sessions.mapped('name')),
                ))

            moves = orders.mapped('account_move')
            posted = moves.filtered(lambda m: m.state == 'posted')
            if moves and wizard.delete_account_move:
                messages.append(_(
                    "Sẽ XOÁ VĨNH VIỄN %(total)s bút toán kế toán (%(posted)s đã vào sổ). "
                    "Việc này tạo lỗ hổng số hiệu chứng từ và phá chuỗi hash bất biến; "
                    "Odoo sẽ cảnh báo 'gap in sequence' ở lần vào sổ tiếp theo.",
                    total=len(moves), posted=len(posted),
                ))
            elif moves:
                messages.append(_(
                    "%s bút toán kế toán được giữ lại, chỉ cắt liên kết tới đơn hàng.",
                    len(moves),
                ))

            pickings = orders.mapped('picking_ids')
            if pickings:
                messages.append(_(
                    "%s phiếu kho được giữ lại và trở thành dữ liệu mồ côi "
                    "(mất tham chiếu tới đơn POS).", len(pickings),
                ))

            if not messages:
                wizard.warning_html = False
                continue
            wizard.warning_html = Markup(
                '<div class="alert alert-danger" role="alert"><ul class="mb-0">%s</ul></div>'
            ) % Markup('').join(
                Markup('<li>%s</li>') % escape(msg) for msg in messages
            )

    @api.depends('order_ids', 'delete_account_move')
    def _compute_impact_html(self):
        for wizard in self:
            if not wizard.order_ids:
                wizard.impact_html = False
                continue
            plan = wizard.order_ids._trcf_hard_delete_preview(wizard.delete_account_move)
            rows = Markup('').join(
                Markup('<tr><td>%s</td><td class="text-end">%s</td></tr>')
                % (escape(table), len(ids))
                for table, dummy, ids in plan['delete']
            )
            nullified = sorted({'%s.%s' % (src, col) for src, col, dummy in plan['nullify']})
            wizard.impact_html = Markup(
                '<table class="table table-sm">'
                '<thead><tr><th>%s</th><th class="text-end">%s</th></tr></thead>'
                '<tbody>%s</tbody></table>'
                '<p class="text-muted small">%s: %s</p>'
            ) % (
                _("Bảng bị xoá dòng"), _("Số dòng"), rows,
                _("Cắt liên kết (SET NULL, chấp nhận mồ côi)"),
                escape(', '.join(nullified) or '-'),
            )

    # ------------------------------------------------------------------
    # Hành động
    # ------------------------------------------------------------------
    def action_hard_delete(self):
        self.ensure_one()
        if (self.confirm_text or '').strip().upper() != HD_CONFIRM_KEYWORD:
            raise UserError(_(
                "Chuỗi xác nhận không đúng. Hãy gõ chính xác: %s", HD_CONFIRM_KEYWORD,
            ))
        if not self.order_ids:
            raise UserError(_("Không còn đơn hàng nào để xoá."))

        count = len(self.order_ids)
        self.order_ids._trcf_hard_delete(
            reason=self.reason, delete_account_move=self.delete_account_move,
        )
        self.env['bus.bus']._sendone(
            self.env.user.partner_id, 'simple_notification', {
                'type': 'danger',
                'title': _("Đã xoá cứng"),
                'message': _("%s đơn hàng POS đã bị xoá vĩnh viễn.", count),
                'sticky': False,
            },
        )
        return {'type': 'ir.actions.client', 'tag': 'soft_reload'}
