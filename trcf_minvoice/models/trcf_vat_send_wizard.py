# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TrcfVatSendWizard(models.TransientModel):
    _name = 'trcf.vat.send.wizard'
    _description = 'VAT Invoice Send Progress Wizard'
    
    order_ids = fields.Many2many('pos.order', string='Orders to Send')
    line_ids = fields.One2many('trcf.vat.send.wizard.line', 'wizard_id', string='Progress Lines')
    
    total_count = fields.Integer(string='Total Orders', compute='_compute_counts', store=True)
    success_count = fields.Integer(string='Success', compute='_compute_counts', store=True)
    failed_count = fields.Integer(string='Failed', compute='_compute_counts', store=True)
    pending_count = fields.Integer(string='Pending', compute='_compute_counts', store=True)
    
    state = fields.Selection([
        ('draft', 'Ready'),
        ('processing', 'Processing'),
        ('done', 'Done')
    ], default='draft', string='Status')
    
    @api.depends('line_ids.status')
    def _compute_counts(self):
        for wizard in self:
            wizard.total_count = len(wizard.line_ids)
            wizard.success_count = len(wizard.line_ids.filtered(lambda l: l.status == 'success'))
            wizard.failed_count = len(wizard.line_ids.filtered(lambda l: l.status == 'failed'))
            wizard.pending_count = len(wizard.line_ids.filtered(lambda l: l.status == 'pending'))
    
    def action_process_invoices(self):
        """Now handled by frontend OWL component for real-time updates"""
        self.state = 'processing'
        return True

    def action_rpc_process_line(self, line_id):
        """RPC method called from JS to process a single line"""
        self.ensure_one()
        line = self.env['trcf.vat.send.wizard.line'].browse(line_id)
        if not line or line.wizard_id.id != self.id:
            return {'success': False, 'error': 'Invalid Line'}
            
        line.status = 'processing'
        self.env.cr.commit()
        
        try:
            result = line.order_id._send_single_vat_invoice()
            if result.get('success'):
                line.write({
                    'status': 'success',
                    'vat_code': result.get('vat_code', '')
                })
            else:
                line.write({
                    'status': 'failed',
                    'error_message': result.get('error', 'Unknown error')
                })
        except Exception as e:
            line.write({
                'status': 'failed',
                'error_message': str(e)
            })
        
        # Check if all done
        self.env.cr.commit()
        self._compute_counts() # Force local update
        if self.pending_count == 0:
            self.state = 'done'
            
        return {
            'success': line.status == 'success',
            'status': line.status,
            'vat_code': line.vat_code,
            'error_message': line.error_message,
            'all_done': self.state == 'done',
            'counts': {
                'success': self.success_count,
                'failed': self.failed_count,
                'pending': self.pending_count
            }
        }


class TrcfVatSendWizardLine(models.TransientModel):
    _name = 'trcf.vat.send.wizard.line'
    _description = 'VAT Send Progress Line'
    _order = 'id'
    
    wizard_id = fields.Many2one('trcf.vat.send.wizard', required=True, ondelete='cascade')
    order_id = fields.Many2one('pos.order', string='Order', required=True)
    order_ref = fields.Char(related='order_id.pos_reference', string='Order #', readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id', string='Currency', readonly=True)
    order_amount = fields.Monetary(related='order_id.amount_total', string='Amount', readonly=True, currency_field='currency_id')
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed')
    ], default='pending', string='Status')
    
    error_message = fields.Text(string='Error Message')
    vat_code = fields.Char(string='VAT Code')
