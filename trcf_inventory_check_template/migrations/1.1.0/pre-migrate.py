# -*- coding: utf-8 -*-
"""
Migration script: Change warehouse_id (stock.warehouse) to location_id (stock.location)

This migration:
1. Renames warehouse_id column to location_id in trcf_inventory_check_template
2. Updates the values from warehouse to warehouse.lot_stock_id (internal location)
3. Renames warehouse_id column to location_id in trcf_inventory_check
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Migration function called by Odoo during module upgrade
    """
    _logger.info("Starting migration: warehouse_id -> location_id")

    try:
        # ========================================
        # 1. Migrate trcf_inventory_check_template
        # ========================================

        # Check if warehouse_id column exists
        cr.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='trcf_inventory_check_template'
            AND column_name='warehouse_id'
        """)

        if cr.fetchone():
            _logger.info("Migrating trcf_inventory_check_template.warehouse_id -> location_id")

            # Add new location_id column
            cr.execute("""
                ALTER TABLE trcf_inventory_check_template
                ADD COLUMN IF NOT EXISTS location_id INTEGER
            """)

            # Migrate data: location_id = warehouse.lot_stock_id
            cr.execute("""
                UPDATE trcf_inventory_check_template AS t
                SET location_id = w.lot_stock_id
                FROM stock_warehouse AS w
                WHERE t.warehouse_id = w.id
                AND t.location_id IS NULL
            """)

            # Drop old warehouse_id column
            cr.execute("""
                ALTER TABLE trcf_inventory_check_template
                DROP COLUMN IF EXISTS warehouse_id CASCADE
            """)

            _logger.info("Successfully migrated trcf_inventory_check_template")
        else:
            _logger.info("Column warehouse_id not found in trcf_inventory_check_template, skipping")

        # ========================================
        # 2. Migrate trcf_inventory_check
        # ========================================

        # Check if warehouse_id column exists and location_id doesn't
        cr.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='trcf_inventory_check'
            AND column_name='warehouse_id'
        """)

        warehouse_exists = cr.fetchone()

        cr.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='trcf_inventory_check'
            AND column_name='location_id'
        """)

        location_exists = cr.fetchone()

        if warehouse_exists and not location_exists:
            _logger.info("Renaming trcf_inventory_check.warehouse_id -> location_id")

            # Simply rename the column (data is already stock.location)
            cr.execute("""
                ALTER TABLE trcf_inventory_check
                RENAME COLUMN warehouse_id TO location_id
            """)

            _logger.info("Successfully renamed trcf_inventory_check.warehouse_id")
        elif location_exists:
            _logger.info("Column location_id already exists in trcf_inventory_check, skipping")
        else:
            _logger.info("Column warehouse_id not found in trcf_inventory_check, skipping")

        _logger.info("Migration completed successfully")

    except Exception as e:
        _logger.error(f"Migration failed: {str(e)}", exc_info=True)
        raise
