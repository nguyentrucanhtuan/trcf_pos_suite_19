# -*- coding: utf-8 -*-
from odoo import fields, models


class TrcfPosHardDeleteLog(models.Model):
    """Nhật ký xoá cứng đơn hàng POS.

    Cố ý KHÔNG có Many2one tới `pos.order`: bản ghi gốc đã bị xoá vĩnh viễn,
    đây là dấu vết duy nhất còn lại để đối soát về sau.
    """
    _name = 'trcf.pos.hard.delete.log'
    _description = 'Nhật ký xoá cứng đơn hàng POS'
    _order = 'delete_date desc, id desc'
    _rec_name = 'order_ref'

    order_ref = fields.Char(string="Số đơn", required=True, index=True)
    deleted_order_id = fields.Integer(string="ID đơn đã xoá", index=True)
    pos_reference = fields.Char(string="Mã tham chiếu POS")
    date_order = fields.Datetime(string="Ngày đặt")
    session_name = fields.Char(string="Phiên bán hàng")
    config_name = fields.Char(string="Điểm bán")
    partner_name = fields.Char(string="Khách hàng")
    amount_total = fields.Float(string="Tổng tiền", digits=(16, 2))
    state_before = fields.Char(string="Trạng thái trước khi xoá")
    account_move_name = fields.Char(string="Hoá đơn liên quan")
    account_move_deleted = fields.Boolean(string="Đã xoá hoá đơn")
    picking_names = fields.Char(string="Phiếu kho giữ lại")

    reason = fields.Text(string="Lý do", required=True)
    user_id = fields.Many2one('res.users', string="Người thực hiện", required=True,
                              default=lambda self: self.env.user, ondelete='restrict')
    delete_date = fields.Datetime(string="Thời điểm xoá", required=True,
                                  default=fields.Datetime.now, index=True)
    batch_uuid = fields.Char(string="Mã lô xoá", index=True,
                             help="Các đơn xoá cùng một lần chia sẻ chung mã lô này.")
    payload_json = fields.Text(string="Snapshot JSON",
                               help="Toàn bộ dữ liệu đơn hàng tại thời điểm xoá.")
    impact_json = fields.Text(string="Bảng tác động",
                              help="Số dòng đã xoá / cắt liên kết theo từng bảng.")
