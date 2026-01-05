# -*- coding: utf-8 -*-
from odoo import models, api
import logging
import re
from html import unescape
from .base import agent_router

_logger = logging.getLogger(__name__)

class MailMessage(models.Model):
    _inherit = 'mail.message'
    
    @api.model_create_multi
    def create(self, vals_list):
        messages = super().create(vals_list)
        
        # Lấy bot partner (giả định có user hoặc dùng partner mặc định)
        bot = self.env['res.users'].sudo().search([
            ('login', '=', 'trcf_ai_assistant')
        ], limit=1)
        
        if not bot:
            return messages
            
        bot_partner_id = bot.partner_id.id
        
        for msg in messages:
            try:
                if (msg.model == 'discuss.channel' and 
                    msg.message_type == 'comment' and
                    msg.author_id.id != bot_partner_id):
                    
                    # Kiểm tra xem có được mention không hoặc trong channel riêng
                    # Tạm thời xử lý mọi tin nhắn trong channel discuss
                    text = re.sub('<[^<]+?>', '', unescape(msg.body or '')).strip()
                    
                    if text:
                        ai_reply = agent_router.route(self.env, text)
                        
                        channel = self.env['discuss.channel'].browse(msg.res_id)
                        channel.message_post(
                            body=ai_reply,
                            author_id=bot_partner_id,
                            message_type='comment',
                            subtype_xmlid='mail.mt_comment'
                        )
            except Exception as e:
                _logger.error(f"❌ Message hook error: {e}")
                
        return messages
