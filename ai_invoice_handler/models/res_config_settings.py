import requests
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AIInvoiceHandlerSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_bookkeeping_debug = fields.Boolean(
        string="Enable AI Bookkeeping Debug Mode",
        config_parameter='ai_invoice_handler.debug'
    )

    assistant_id = fields.Char(
        string="OpenAI Assistant ID",
        default=lambda self: self.env['ir.config_parameter'].sudo().get_param('openai.assistant_id', default=""),
        config_parameter='openai.assistant_id'
    )

    def action_update_assistant(self):
        """ Create or Update Assistant in OpenAI API """
        api_key = self.env['ir.config_parameter'].sudo().get_param('openai.api_key')
        if not api_key:
            raise UserError(_("OpenAI API Key is missing. Please configure it in settings."))

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'OpenAI-Beta': 'assistants=v2'
        }

        # Fetch all bookkeeping accounts for reference
        accounts = self.env["account.account"].search([])
        account_mapping = {str(acc.id): acc.name for acc in accounts}  # Create an ID-to-name mapping
        # Convert account mapping to JSON
        account_mapping_json = json.dumps(account_mapping, indent=2)


        instructions = f"""
            ### Account Mapping (Reference for Account Selection):
            {account_mapping_json}
        """

        payload = {
            "name": "Odoo Assistant",
            "instructions": instructions,
            "model": "gpt-4-turbo"
        }

        assistant_id = self.env['ir.config_parameter'].sudo().get_param('openai.assistant_id')

        if assistant_id:
            # Update existing assistant
            url = f"https://api.openai.com/v1/assistants/{assistant_id}"
            response = requests.post(url, headers=headers, json=payload)
        else:
            # Create new assistant
            url = "https://api.openai.com/v1/assistants"
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                assistant_id = response.json().get("id")
                self.env['ir.config_parameter'].sudo().set_param('openai.assistant_id', assistant_id)
                self.assistant_id = assistant_id  # ✅ Update UI with new assistant ID

        if response.status_code != 200:
            error_msg = response.json().get("error", {}).get("message", "Unknown error")
            raise UserError(_("Error syncing assistant: %s") % error_msg)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Assistant updated successfully!'),
                'sticky': False,
            }
        }
