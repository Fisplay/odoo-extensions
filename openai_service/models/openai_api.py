import openai
from odoo import models, fields, api

class OpenAIService(models.Model):
    _name = "openai.service"
    _description = "OpenAI API Service"

    api_key = fields.Char(string="API Key", required=True)

    @api.model
    def get_openai_response(self, prompt):
        """Call OpenAI API and return response using the latest API format."""
        api_key = self.env["ir.config_parameter"].sudo().get_param("openai.api_key")
        if not api_key:
            return "API key not configured"

        try:
            client = openai.OpenAI(api_key=api_key)  # NEW client format
            response = client.chat.completions.create(  # Updated method
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content  # Corrected response format
        except Exception as e:
            return f"Error: {str(e)}"
