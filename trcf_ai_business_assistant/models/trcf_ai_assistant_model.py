# -*- coding: utf-8 -*-
from odoo import models, api, fields
import logging
import re
from html import unescape
from datetime import timedelta

# from google import genai
from google import generativeai as genai

# from google.genai import types

_logger = logging.getLogger(__name__)

class TrcfAIBusinessAssistant(models.Model):
    _inherit = 'mail.message'
    
    @api.model_create_multi
    def create(self, vals_list):
        """Bắt tin nhắn và auto reply"""
        
        # Tạo messages
        messages = super().create(vals_list)
                
        # Lấy bot user
        bot = self.env['res.users'].sudo().search([
            ('login', '=', 'trcf_ai_business_assistant')
        ], limit=1)
        
        if not bot:
            return messages
        
        bot_partner_id = bot.partner_id.id
        
        # Xử lý từng message
        for msg in messages:
            try:
                # Chỉ xử lý tin nhắn trong discuss channel, bỏ qua tin nhắn của bot
                if (msg.model == 'discuss.channel' and 
                    msg.res_id and 
                    msg.message_type == 'comment' and
                    msg.author_id.id != bot_partner_id):
                    
                    # Lấy nội dung
                    text = re.sub('<[^<]+?>', '', unescape(msg.body or '')).strip()
                    
                    if text:
                        _logger.info(f"💬 Received: {text}")

                        # ✅ Gọi AI để lấy reply
                        ai_reply = self._call_gemini_ai(text)

                        # Reply đơn giản
                        channel = self.env['discuss.channel'].browse(msg.res_id)
                        reply_msg = channel.message_post(
                            body=ai_reply,
                            author_id=bot_partner_id,
                            message_type='comment',
                            subtype_xmlid='mail.mt_comment'
                        )

            except Exception as e:
                _logger.error(f"❌ {e}")
        
        return messages

    def _call_gemini_ai(self, user_message):

        # Configure the client and tools
        api_key = "AIzaSyB5j2n5tmoQLQWfNaTF3Yi4k9nLxrP4qgA"
        #api_key = self.env['ir.config_parameter'].sudo().get_param('trcf.gemini_api_key')
        if not api_key:
            return "⚠️ Chưa cấu hình API Key"

        client = genai.Client(api_key=api_key)

        # Lấy function declarations từ business functions
        function_declarations = self.env['trcf.business.functions']._get_function_declarations()

        # Configure tools
        tools = types.Tool(function_declarations=function_declarations)
        config = types.GenerateContentConfig(
            tools=[tools],
            temperature=0.1,
            system_instruction="""Bạn là trợ lý kinh doanh cho quán cà phê.
Trả lời ngắn gọn, thân thiện bằng tiếng Việt.
Dùng function get_revenue khi cần dữ liệu doanh thu."""
        )

        # Send request with function declarations
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config=config,
        )

        if not response.candidates:
            return "⚠️ Không có phản hồi"

        part = response.candidates[0].content.parts[0]
        if hasattr(part, 'function_call') and part.function_call:
            function_name = part.function_call.name
            function_args = part.function_call.args


            result = self._execute_function(function_name, function_args)

            final_response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    user_message,
                    response.candidates[0].content,
                    types.Content(
                        role="function",
                        parts=[types.Part(
                            function_response=types.FunctionResponse(
                                name=function_name,
                                response={"result": result}
                            )
                        )]
                    )
                ],
                config=config
            )
            # Trả về text reply tự nhiên
            return final_response.candidates[0].content.parts[0].text if final_response.candidates else "⚠️ Lỗi"

        else:
            # Không có function call - trả text trực tiếp
            return part.text if part.text else "⚠️ Không hiểu"

    def _execute_function(self, func_name, func_args):
        """Thực thi function và trả về kết quả"""
        try:
            _logger.info(f"📞 Executing: {func_name}({func_args})")
            
            if func_name == 'get_revenue':
                # Gọi hàm get_revenue từ business functions
                result = self.env['trcf.business.functions']._get_revenue(
                    start_date=func_args.get('start_date'),
                    end_date=func_args.get('end_date')
                )
                
                _logger.info(f"✅ Result: {result}")
                return result
            
            else:
                # Function không tồn tại
                error_result = {'error': f'Unknown function: {func_name}'}
                _logger.error(f"❌ {error_result}")
                return error_result
                
        except Exception as e:
            error_result = {'error': str(e)}
            _logger.error(f"❌ Function execution error: {e}")
            return error_result
