# -*- coding: utf-8 -*-
{
    'name': "Invoice AI Handler",

    'summary': """
        Automatically set bookeeping accounts, taxes, and analytic accounts on invoices""",
    'description': """
        Automatically set bookeeping accounts, taxes, and analytic accounts on invoices. Check 10 previous as reference.
    """,

    'author': "Fisplay Oy",
    'website': "https://fisplay.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'AI',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'account_accountant','openai_service'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_move_action.xml',
    ],
}
