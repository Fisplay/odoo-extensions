from odoo import models, fields

class OpenaiServiceModuleSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # OpenAI Service Section
    openai_api_key = fields.Char(
        string="OpenAI API Key",
        config_parameter='openai.api_key',
        group="base.group_system"  # ✅ Fix: Ensures settings appear under "System Settings"
    )
