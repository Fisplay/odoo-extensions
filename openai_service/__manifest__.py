{
    "name": "OpenAI Service",
    "version": "1.0",
    "summary": "Integrate OpenAI API with Odoo to generate AI-driven content and automate workflows.",
    "category": "Tools",
    "author": "Fisplay Oy",
    "license": "LGPL-3",
    "website": "https://fisplay.com",
    "depends": ["base"],
    "data": [],
    "installable": True,
    "application": False,
    "description": """
OpenAI Service Module for Odoo 16
=================================
This module integrates OpenAI's GPT API into Odoo, enabling AI-driven automation and content generation.

Features:
---------
- Generate AI-powered responses using OpenAI's models (e.g., GPT-3.5, GPT-4).
- Seamless integration with Odoo Server Actions for automated AI tasks.
- Post AI-generated messages to Chatter as OdooBot or a custom user.
- Secure API key management via Odoo’s system parameters.

How to Use:
-----------
1. Configure OpenAI API key in System Parameters:
   - Key: `openai.api_key`
   - Value: `your-openai-api-key`
2. Create a Server Action (Python Code) to call OpenAI for automation.
3. Automate AI-generated messages in Chatter.
4. Use AI for content generation, sales insights, or support automation.

Example Usage:
--------------
- AI-powered customer support responses in Chatter.
- AI-generated summaries for leads, orders, or tickets.
- Automated AI replies in discussions and help desks.
- Data processing and analysis using OpenAI.

Installation & Setup:
---------------------
1. Install the module from Odoo Apps.
2. Configure OpenAI API key under System Parameters.
3. Create Server Actions using AI prompts.
4. Start automating workflows with AI!

Requirements:
-------------
- Odoo 16 (Community or Enterprise)
- OpenAI API Key (https://platform.openai.com)
- Python `openai` package (`pip install openai` if needed)

""",
}
