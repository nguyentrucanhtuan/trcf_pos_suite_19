# -*- coding: utf-8 -*-
"""
Marketing Content Model - Lưu và quản lý content với workflow duyệt
"""
from odoo import models, fields, api
import json


class TrcfMarketingContent(models.Model):
    _name = 'trcf.marketing.content'
    _description = 'Marketing Content'
    _order = 'create_date desc'

    name = fields.Char(string="Tiêu đề", required=True)
    
    # Platform Selection
    platform = fields.Selection([
        ('tiktok', 'TikTok'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('threads', 'Threads'),
    ], string="Platform", required=True, default='instagram')
    
    # Content Data
    pillar = fields.Char(string="Content Pillar")
    angle = fields.Char(string="Angle")
    content = fields.Html(string="Nội dung")
    hashtags = fields.Char(string="Hashtags")
    
    # Hook for TikTok/Reels
    hook = fields.Char(string="Hook")
    
    # Approval Status
    state = fields.Selection([
        ('draft', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối')
    ], string="Trạng thái", default='draft', required=True)
    
    approval_date = fields.Datetime(string="Ngày duyệt", readonly=True)
    rejection_reason = fields.Text(string="Lý do từ chối")
    
    # Metadata for AI learning
    used_keywords = fields.Text(string="Keywords đã dùng", help="JSON array")
    
    def action_approve(self):
        """Duyệt content"""
        self.write({
            'state': 'approved',
            'approval_date': fields.Datetime.now()
        })
        return {'type': 'ir.actions.client', 'tag': 'reload'}
    
    def action_reject(self):
        """Mở wizard nhập lý do từ chối"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lý do từ chối',
            'res_model': 'trcf.marketing.content.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_content_id': self.id}
        }
    
    @api.model
    def get_approved_history(self, limit=10):
        """Lấy content đã duyệt để AI học"""
        approved = self.search([
            ('state', '=', 'approved')
        ], limit=limit, order='approval_date desc')
        
        return [{
            'name': c.name,
            'pillar': c.pillar,
            'angle': c.angle,
            'hook': c.hook,
            'platform': c.platform,
        } for c in approved]
    
    @api.model
    def get_rejected_history(self, limit=10):
        """Lấy content bị từ chối để AI tránh"""
        rejected = self.search([
            ('state', '=', 'rejected')
        ], limit=limit, order='create_date desc')
        
        return [{
            'name': c.name,
            'pillar': c.pillar,
            'angle': c.angle,
            'hook': c.hook,
            'reason': c.rejection_reason,
        } for c in rejected]
    
    @api.model
    def action_generate_content(self):
        """Mở wizard tạo content mới bằng AI"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tạo Content với AI',
            'res_model': 'trcf.marketing.content.generate.wizard',
            'view_mode': 'form',
            'target': 'new',
        }


class TrcfMarketingContentGenerateWizard(models.TransientModel):
    _name = 'trcf.marketing.content.generate.wizard'
    _description = 'Content Generation Wizard'

    platform_tiktok = fields.Boolean(string="TikTok", default=True)
    platform_instagram = fields.Boolean(string="Instagram", default=True)
    platform_facebook = fields.Boolean(string="Facebook", default=True)
    platform_threads = fields.Boolean(string="Threads", default=True)
    
    custom_request = fields.Text(
        string="Yêu cầu cụ thể",
        placeholder="VD: Tạo content về món Cold Brew mới ra mắt..."
    )
    
    def action_generate(self):
        """Gọi AI để tạo content"""
        from .agents.agent import MarketingContentAgent
        
        # Collect selected platforms
        platforms = []
        if self.platform_tiktok:
            platforms.append('tiktok')
        if self.platform_instagram:
            platforms.append('instagram')
        if self.platform_facebook:
            platforms.append('facebook')
        if self.platform_threads:
            platforms.append('threads')
        
        if not platforms:
            platforms = ['instagram']
        
        # Create agent and generate
        agent = MarketingContentAgent(self.env)
        result = agent.generate_content(
            platforms=platforms,
            request=self.custom_request
        )
        
        if result.get('success') and result.get('created_ids'):
            # Open the created content
            return {
                'type': 'ir.actions.act_window',
                'name': 'Content đã tạo',
                'res_model': 'trcf.marketing.content',
                'view_mode': 'list,form',
                'domain': [('id', 'in', result['created_ids'])],
                'target': 'current',
            }
        else:
            # Show error
            raise models.ValidationError(result.get('error', 'Có lỗi xảy ra'))


class TrcfMarketingContentRejectWizard(models.TransientModel):
    _name = 'trcf.marketing.content.reject.wizard'
    _description = 'Rejection Wizard'

    content_id = fields.Many2one('trcf.marketing.content', string="Content", required=True)
    rejection_reason = fields.Text(string="Lý do từ chối", required=True)

    def action_confirm_reject(self):
        """Xác nhận từ chối với lý do"""
        self.content_id.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason
        })
        return {'type': 'ir.actions.client', 'tag': 'reload'}
