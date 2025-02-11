{
    "name": "AI Invoice Bookkeeping Assist",
    "summary": "Automate bookkeeping account, analytic distribution, and tax selection for vendor invoices using AI.",
    "description": """
AI Invoice Bookkeeping Assist helps streamline bookkeeping by automatically selecting the correct account, analytic distribution, and tax based on historical vendor invoices. 

### Features:
- Automatically assigns bookkeeping accounts based on past invoices.  
- Suggests analytic distributions and tax rates using AI.  
- Fetches the last 5 purchase invoices for reference.  
- Ensures accurate account selection by mapping account IDs to names.  
- Prevents modifications on non-draft invoices.  
- Debugging: Posts AI prompts into the invoice chatter for transparency.  
- Contextual Action: Available only on vendor invoices (not sales invoices).  

This module helps accountants and finance teams save time and reduce errors by leveraging AI for bookkeeping automation.
    """,
    "author": "Fisplay Oy",
    "website": "https://fisplay.com",
    "category": "Accounting",
    "version": "1.0",
    "license": "LGPL-3",
    'depends': ['base', 'account', 'account_accountant','openai_service'],
    "data": [
        "views/account_move_action.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
