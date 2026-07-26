# -*- coding: utf-8 -*-
"""Engine xoá cứng (raw SQL) dùng chung.

Odoo chặn xoá nhiều bản ghi bằng `@api.ondelete` ở tầng ORM. Engine này bỏ qua
tầng ORM và thao tác thẳng trên Postgres, nên phải tự lo toàn bộ đồ thị khoá
ngoại. Thay vì hard-code danh sách bảng (sẽ lạc hậu ngay khi cài thêm module),
engine dò `pg_constraint` lúc chạy và tự suy ra hành động cho từng khoá ngoại.
"""

import logging
from collections import defaultdict

from odoo import _, api, models, tools
from odoo.exceptions import UserError
from odoo.tools import SQL
from odoo.tools.sql import existing_tables

_logger = logging.getLogger(__name__)

# Số id tối đa đưa vào một câu lệnh SQL, tránh statement quá lớn.
HD_CHUNK_SIZE = 500

# Độ sâu đệ quy tối đa khi lan theo khoá ngoại. Đồ thị FK của Odoo nông
# (thường <= 4 tầng); ngưỡng này chỉ để chặn vòng lặp bất thường.
HD_MAX_DEPTH = 12

# Bảng master: tuyệt đối không xoá dòng. Nếu khoá ngoại trỏ tới đối tượng bị
# xoá là NULLABLE thì SET NULL, còn NOT NULL thì dừng lại báo lỗi thay vì âm
# thầm phá dữ liệu gốc.
HD_NEVER_DELETE = frozenset({
    'ir_model', 'ir_model_fields', 'ir_module_module', 'ir_ui_view',
    'ir_act_window', 'ir_act_server', 'ir_cron', 'ir_sequence',
    'res_company', 'res_users', 'res_partner', 'res_currency', 'res_country',
    'product_product', 'product_template', 'product_category',
    'uom_uom', 'account_account', 'account_journal', 'account_tax',
    'stock_location', 'stock_warehouse', 'stock_valuation_layer',
    'stock_quant', 'hr_employee', 'pos_config', 'pos_session',
})

# Các model có dữ liệu "gắn kèm" theo res_model/res_id nhưng không có khoá
# ngoại thật, Postgres không dọn hộ. mail_tracking_value / mail_notification
# không cần liệt kê vì cascade theo mail_message.
HD_GENERIC_TABLES = (
    ('ir_attachment', 'res_model', 'res_id'),
    ('mail_message', 'model', 'res_id'),
    ('mail_followers', 'res_model', 'res_id'),
    ('mail_activity', 'res_model', 'res_id'),
    ('rating_rating', 'res_model', 'res_id'),
    ('ir_model_data', 'model', 'res_id'),
)


class TrcfHardDeleteEngine(models.AbstractModel):
    _name = 'trcf.hard.delete.engine'
    _description = 'Engine xoá cứng bằng SQL'

    # ------------------------------------------------------------------
    # Dò lược đồ
    # ------------------------------------------------------------------
    @api.model
    @tools.ormcache()
    def _hd_fk_graph(self):
        """Đồ thị khoá ngoại đảo chiều của toàn bộ schema.

        :return: dict ``{bảng_đích: [(bảng_nguồn, cột, notnull, confdeltype)]}``
            trong đó ``confdeltype`` là ``'c'`` (cascade), ``'n'`` (set null),
            ``'r'`` (restrict), ``'a'`` (no action), ``'d'`` (set default).
        """
        self.env.cr.execute(SQL("""
            SELECT c.confrelid::regclass::text AS tgt_table,
                   c.conrelid::regclass::text  AS src_table,
                   a.attname                   AS src_col,
                   a.attnotnull                AS not_null,
                   c.confdeltype               AS del_type
              FROM pg_constraint c
              JOIN pg_attribute a
                ON a.attrelid = c.conrelid
               AND a.attnum = ANY (c.conkey)
             WHERE c.contype = 'f'
               AND array_length(c.conkey, 1) = 1
        """))
        graph = defaultdict(list)
        for tgt, src, col, notnull, del_type in self.env.cr.fetchall():
            graph[tgt].append((src, col, notnull, del_type))
        return {k: tuple(v) for k, v in graph.items()}

    @api.model
    @tools.ormcache()
    def _hd_tables_with_id(self):
        """Tập các bảng có cột ``id`` (bảng many2many quan hệ thì không có)."""
        self.env.cr.execute(SQL("""
            SELECT c.relname
              FROM pg_class c
              JOIN pg_namespace n ON n.oid = c.relnamespace
              JOIN pg_attribute a ON a.attrelid = c.oid
             WHERE c.relkind = 'r'
               AND n.nspname = current_schema
               AND a.attname = 'id'
               AND a.attnum > 0
        """))
        return frozenset(row[0] for row in self.env.cr.fetchall())

    @api.model
    @tools.ormcache()
    def _hd_existing_generic_tables(self):
        """Chỉ giữ lại các bảng generic thực sự tồn tại trong DB hiện tại.

        `rating_rating`, `mail_activity`... chỉ có khi module tương ứng được
        cài, nên không thể xoá mù quáng.
        """
        names = tuple(table for table, dummy_m, dummy_r in HD_GENERIC_TABLES)
        return tuple(
            entry for entry in HD_GENERIC_TABLES
            if entry[0] in set(existing_tables(self.env.cr, names))
        )

    @api.model
    @tools.ormcache()
    def _hd_table_to_model(self):
        """Ánh xạ ``tên_bảng -> tên_model`` cho các model thật của Odoo."""
        self.env.cr.execute(SQL("SELECT model FROM ir_model"))
        return {m.replace('.', '_'): m for (m,) in self.env.cr.fetchall()}

    # ------------------------------------------------------------------
    # Lập kế hoạch
    # ------------------------------------------------------------------
    @api.model
    def _hd_build_plan(self, seeds, keep_tables=()):
        """Suy ra kế hoạch xoá đầy đủ từ tập bản ghi gốc.

        :param dict seeds: ``{tên_bảng: iterable id}`` các bản ghi cần xoá.
        :param keep_tables: các bảng phải giữ lại dòng dù khoá ngoại có cascade.
        :return: dict với các khoá ``delete`` (list ``(bảng, depth, ids)``),
            ``nullify`` (list ``(bảng, cột, bảng_đích)``) và
            ``rel_delete`` (list ``(bảng, cột, bảng_đích)``).
        """
        graph = self._hd_fk_graph()
        with_id = self._hd_tables_with_id()
        keep_tables = frozenset(keep_tables)

        resolved = defaultdict(set)     # bảng -> ids sẽ xoá
        depth_of = {}                   # bảng -> độ sâu lớn nhất đã gặp
        nullify = []
        rel_delete = []
        seen_nullify = set()
        seen_rel = set()

        pending = [(table, set(ids), 0) for table, ids in seeds.items() if ids]
        while pending:
            table, ids, depth = pending.pop(0)
            if depth > HD_MAX_DEPTH:
                raise UserError(_(
                    "Đồ thị khoá ngoại quá sâu tại bảng '%s'. Dừng để tránh "
                    "xoá lan không kiểm soát.", table,
                ))
            new_ids = ids - resolved[table]
            if not new_ids:
                continue
            resolved[table] |= new_ids
            depth_of[table] = max(depth_of.get(table, 0), depth)

            for src_table, src_col, not_null, del_type in graph.get(table, ()):
                protected = src_table in HD_NEVER_DELETE or src_table in keep_tables
                must_die = not_null or del_type == 'c'

                if protected:
                    if not_null:
                        raise UserError(_(
                            "Không thể xoá: bảng bắt buộc giữ lại '%(src)s' có cột "
                            "'%(col)s' NOT NULL trỏ tới '%(tgt)s'. Hãy bỏ chọn "
                            "tuỳ chọn giữ lại bảng này hoặc xử lý thủ công.",
                            src=src_table, col=src_col, tgt=table,
                        ))
                    key = (src_table, src_col, table)
                    if key not in seen_nullify:
                        seen_nullify.add(key)
                        nullify.append(key)
                    continue

                if not must_die:
                    key = (src_table, src_col, table)
                    if key not in seen_nullify:
                        seen_nullify.add(key)
                        nullify.append(key)
                    continue

                # Bảng quan hệ many2many: không có id, xoá thẳng theo cột.
                if src_table not in with_id:
                    key = (src_table, src_col, table)
                    if key not in seen_rel:
                        seen_rel.add(key)
                        rel_delete.append(key)
                    continue

                child_ids = self._hd_select_children(src_table, src_col, new_ids)
                if child_ids:
                    pending.append((src_table, child_ids, depth + 1))

        # Xoá từ lá lên gốc: bảng phát hiện ở độ sâu lớn hơn phải xoá trước.
        delete_plan = sorted(
            ((t, depth_of[t], sorted(ids)) for t, ids in resolved.items() if ids),
            key=lambda item: -item[1],
        )
        return {'delete': delete_plan, 'nullify': nullify, 'rel_delete': rel_delete}

    @api.model
    def _hd_select_children(self, table, column, parent_ids):
        """Lấy id các dòng của ``table`` trỏ tới ``parent_ids`` qua ``column``."""
        result = set()
        for chunk in self._hd_chunks(sorted(parent_ids)):
            self.env.cr.execute(SQL(
                "SELECT id FROM %s WHERE %s IN %s",
                SQL.identifier(table), SQL.identifier(column), tuple(chunk),
            ))
            result.update(row[0] for row in self.env.cr.fetchall())
        return result

    @staticmethod
    def _hd_chunks(ids):
        ids = list(ids)
        for index in range(0, len(ids), HD_CHUNK_SIZE):
            yield ids[index:index + HD_CHUNK_SIZE]

    # ------------------------------------------------------------------
    # Thực thi
    # ------------------------------------------------------------------
    @api.model
    def _hd_execute(self, plan):
        """Chạy kế hoạch xoá. Toàn bộ nằm trong transaction hiện tại.

        Thứ tự bắt buộc: cắt liên kết (SET NULL) -> xoá bảng quan hệ ->
        xoá dữ liệu đính kèm generic -> xoá bản ghi từ lá lên gốc.
        """
        by_table = {table: ids for table, _depth, ids in plan['delete']}
        counters = defaultdict(int)

        for src_table, src_col, tgt_table in plan['nullify']:
            target_ids = by_table.get(tgt_table)
            if not target_ids:
                continue
            for chunk in self._hd_chunks(target_ids):
                self.env.cr.execute(SQL(
                    "UPDATE %s SET %s = NULL WHERE %s IN %s",
                    SQL.identifier(src_table), SQL.identifier(src_col),
                    SQL.identifier(src_col), tuple(chunk),
                ))
                counters['nullify:%s.%s' % (src_table, src_col)] += self.env.cr.rowcount

        for src_table, src_col, tgt_table in plan['rel_delete']:
            target_ids = by_table.get(tgt_table)
            if not target_ids:
                continue
            for chunk in self._hd_chunks(target_ids):
                self.env.cr.execute(SQL(
                    "DELETE FROM %s WHERE %s IN %s",
                    SQL.identifier(src_table), SQL.identifier(src_col), tuple(chunk),
                ))
                counters['rel:%s' % src_table] += self.env.cr.rowcount

        self._hd_clean_generic(by_table, counters)

        for table, _depth, ids in plan['delete']:
            for chunk in self._hd_chunks(ids):
                self.env.cr.execute(SQL(
                    "DELETE FROM %s WHERE id IN %s",
                    SQL.identifier(table), tuple(chunk),
                ))
                counters[table] += self.env.cr.rowcount

        return dict(counters)

    @api.model
    def _hd_clean_generic(self, by_table, counters):
        """Dọn attachment / message / follower... trỏ tới bản ghi bị xoá."""
        table_to_model = self._hd_table_to_model()
        generic_tables = self._hd_existing_generic_tables()
        for table, ids in by_table.items():
            model_name = table_to_model.get(table)
            if not model_name:
                continue
            for gen_table, model_col, res_col in generic_tables:
                for chunk in self._hd_chunks(ids):
                    self.env.cr.execute(SQL(
                        "DELETE FROM %s WHERE %s = %s AND %s IN %s",
                        SQL.identifier(gen_table), SQL.identifier(model_col),
                        model_name, SQL.identifier(res_col), tuple(chunk),
                    ))
                    counters['generic:%s' % gen_table] += self.env.cr.rowcount

    # ------------------------------------------------------------------
    # API công khai
    # ------------------------------------------------------------------
    @api.model
    def hd_run(self, seeds, keep_tables=(), dry_run=False):
        """Lập kế hoạch và (tuỳ chọn) thực thi xoá cứng.

        :param dict seeds: ``{tên_bảng: iterable id}``.
        :param keep_tables: bảng cần giữ lại dòng (sẽ SET NULL thay vì xoá).
        :param bool dry_run: chỉ trả kế hoạch, không đụng dữ liệu.
        :return: ``(plan, counters)``; ``counters`` rỗng khi ``dry_run``.
        """
        self.env.flush_all()
        plan = self._hd_build_plan(seeds, keep_tables=keep_tables)
        if dry_run:
            return plan, {}
        counters = self._hd_execute(plan)
        self.env.invalidate_all()
        self.env.registry.clear_cache()
        _logger.warning(
            "TRCF hard delete by uid=%s: %s", self.env.uid,
            ', '.join('%s=%s' % kv for kv in sorted(counters.items()) if kv[1]),
        )
        return plan, counters
