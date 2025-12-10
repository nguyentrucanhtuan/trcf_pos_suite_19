from odoo import api, models, fields
import logging

_logger = logging.getLogger(__name__)


class TrcfMomoTransaction(models.Model):
    """
    Store pending MoMo payment transactions for webhook matching
    """
    _name = 'trcf.momo.transaction'
    _description = 'MoMo Payment Transaction'
    _order = 'create_date desc'

    # Order info
    pos_order_ref = fields.Char('POS Order Reference', index=True)
    pos_session_id = fields.Many2one('pos.session', 'POS Session')
    pos_config_id = fields.Many2one('pos.config', 'POS Config')
    
    # MoMo transaction info
    momo_order_id = fields.Char('MoMo Order ID', required=True, index=True)
    momo_request_id = fields.Char('MoMo Request ID')
    amount = fields.Float('Amount')
    
    # Status
    status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ], default='pending', string='Status')
    
    # Webhook data
    result_code = fields.Integer('Result Code')
    message = fields.Char('Message')
    trans_id = fields.Char('MoMo Transaction ID')
    
    # Timestamps
    payment_time = fields.Datetime('Payment Time')

    @api.model
    def create_pending_transaction(self, pos_order_ref, momo_order_id, amount, 
                                    request_id=None, session_id=None, config_id=None):
        """Create a pending transaction record"""
        return self.create({
            'pos_order_ref': pos_order_ref,
            'momo_order_id': momo_order_id,
            'momo_request_id': request_id,
            'amount': amount,
            'pos_session_id': session_id,
            'pos_config_id': config_id,
            'status': 'pending',
        })

    @api.model
    def update_from_ipn(self, momo_order_id, result_code, message, trans_id=None):
        """Update transaction from IPN webhook"""
        transaction = self.search([('momo_order_id', '=', momo_order_id)], limit=1)
        if not transaction:
            _logger.warning(f"MoMo IPN: Transaction not found for order {momo_order_id}")
            return False
        
        # Update status based on result code
        status = 'success' if result_code == 0 else 'failed'
        
        transaction.write({
            'status': status,
            'result_code': result_code,
            'message': message,
            'trans_id': trans_id,
            'payment_time': fields.Datetime.now(),
        })
        
        _logger.info(f"MoMo IPN: Updated transaction {momo_order_id} to {status}")
        
        # Send notification via bus if successful
        if status == 'success':
            self._notify_pos_payment_success(transaction)
        
        return transaction

    def _notify_pos_payment_success(self, transaction):
        """Send bus notification to POS about successful payment"""
        if not transaction.pos_config_id:
            _logger.warning("MoMo: No pos_config_id to send notification")
            return
            
        config = transaction.pos_config_id
        
        # Odoo 19 POS uses access_token based channels
        # Format: access_token-NOTIFICATION_NAME
        if config.access_token:
            channel = config.access_token
            notification_name = f"{config.access_token}-MOMO_PAYMENT_SUCCESS"
            
            self.env['bus.bus']._sendone(channel, notification_name, {
                'pos_order_ref': transaction.pos_order_ref,
                'momo_order_id': transaction.momo_order_id,
                'amount': transaction.amount,
                'trans_id': str(transaction.trans_id),
            })
            
            _logger.info(f"MoMo: Sent bus notification to channel {channel} for order {transaction.pos_order_ref}")
        else:
            _logger.warning(f"MoMo: Config {config.id} has no access_token")
