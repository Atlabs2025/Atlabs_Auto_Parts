# -*- coding: utf-8 -*-
{
    'name': "Odoo Customer, Supplier/Vendor (Partner) Account Statement (SoA)",

    'summary': """
         Extend functioality for account statements (SoA)""",

    'description': """
        This will be used for the partner (customer/supplier/vendor) account statement in the system.
    """,

    'author': "odooflex",
    'website': "www.odooflex.com",
    'images': ["static/description/account_state.png"],

    'category': 'Accounting',
    'version': '15.0.1',
    'depends': ['account', 'base'],
    'license': 'AGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'security/acc_state_security.xml',
        'views/acc_statement_view.xml',
        'views/report_cust_acc_stat.xml',
        'views/report_supp_acc_stat.xml',
        'views/reports.xml',
        # 'data/mail_data.xml',
    ],

    'installable': True,
    'application': True,
    'price':  10,
    'currency': "USD",
}
