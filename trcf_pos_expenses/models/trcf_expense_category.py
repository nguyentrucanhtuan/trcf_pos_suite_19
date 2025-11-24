# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TrcfExpenseCategory(models.Model):
    _name = 'trcf.expense.category'
    _description = 'Expense Category'
    _order = 'name'

    name = fields.Char(
        string='Category Name',
        required=True,
        help='Name of the expense category'
    )
    
    trcf_code = fields.Char(
        string='Category Code',
        help='Short code for the category'
    )
    
    trcf_description = fields.Text(
        string='Description',
        help='Detailed description of the category'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to archive the category'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    
    trcf_expense_count = fields.Integer(
        string='Expense Count',
        compute='_compute_trcf_expense_count'
    )
    
    @api.depends('name')
    def _compute_trcf_expense_count(self):
        for category in self:
            category.trcf_expense_count = self.env['trcf.expense'].search_count([
                ('trcf_category_id', '=', category.id)
            ])
    
    @api.model
    def _add_sql_constraints(self):
        """Add SQL constraints using the new Odoo 19 method"""
        self.env.cr.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'trcf_expense_category_code_unique'
                ) THEN
                    ALTER TABLE trcf_expense_category 
                    ADD CONSTRAINT trcf_expense_category_code_unique 
                    UNIQUE (trcf_code, company_id);
                END IF;
            END $$;
        """)
