# -*- coding: utf-8 -*-
"""
MAIL MESSAGE HOOK - Bắt tin nhắn và route đến agent
Refactor từ trcf_ai_assistant_model.py
"""
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
        """Hook tin nhắn và auto reply qua Agent Router"""
        
        # Tạo messages
        messages = super().create(vals_list)
        
        # Lấy bot user
        # Tìm bot user - Trợ lý Sáng tạo Thức uống
        bot = self.env['res.users'].sudo().search([
            ('login', '=', 'trcf_drink_creative_assistant')
        ], limit=1)
        
        if not bot:
            return messages
        
        bot_partner_id = bot.partner_id.id
        
        # Xử lý từng message
        for msg in messages:
            try:
                # Chỉ xử lý tin nhắn trong discuss channel
                if (msg.model == 'discuss.channel' and 
                    msg.res_id and 
                    msg.message_type == 'comment' and
                    msg.author_id.id != bot_partner_id):
                    
                    # Lấy nội dung text
                    text = re.sub('<[^<]+?>', '', unescape(msg.body or '')).strip()
                    
                    if text:
                        _logger.info(f"💬 Received: {text}")
                        
                        # Gọi Agent Router
                        ai_reply = agent_router.route(self.env, text)
                        
                        # Reply vào channel
                        channel = self.env['discuss.channel'].browse(msg.res_id)
                        channel.message_post(
                            body=ai_reply,
                            author_id=bot_partner_id,
                            message_type='comment',
                            subtype_xmlid='mail.mt_comment'
                        )
                        
            except Exception as e:
                _logger.error(f"❌ Message hook error: {e}", exc_info=True)
        
        return messages
