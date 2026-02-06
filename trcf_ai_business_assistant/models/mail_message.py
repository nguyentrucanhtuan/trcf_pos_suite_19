# -*- coding: utf-8 -*-
from odoo import models, api
import logging
import re
from html import unescape
from markupsafe import Markup
from .base import agent_router

_logger = logging.getLogger(__name__)

def markdown_to_html(text):
    """Convert simple Markdown to HTML for Odoo Discuss"""
    if not text:
        return text
    
    # Convert line breaks to <br/>
    html = text.replace('\n', '<br/>')
    
    # Convert **bold** to <strong>bold</strong>
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # Convert *italic* to <em>italic</em>
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Convert `code` to <code>code</code>
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
    
    # Wrap in paragraph and mark as safe
    html = f'<p>{html}</p>'
    
    return Markup(html)

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
                        
                        # Convert Markdown to HTML
                        ai_reply_html = markdown_to_html(ai_reply)
                        
                        channel = self.env['discuss.channel'].browse(msg.res_id)
                        channel.message_post(
                            body=ai_reply_html,
                            author_id=bot_partner_id,
                            message_type='comment',
                            subtype_xmlid='mail.mt_comment'
                        )
            except Exception as e:
                _logger.error(f"❌ Message hook error: {e}")
                
        return messages

