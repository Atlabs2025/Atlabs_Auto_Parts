# -*- coding: utf-8 -*-
{
    'name': 'RFQ',
    'version': '18.0.1.0.0',
    'category': 'Request For Quotation',
    'summary': 'Request For Quotation',
    'description': 'rfq',
    'depends': [
        'contacts','product','stock','purchase','stock','sale',
    ],
'data': [
    'security/ir.model.access.csv',
    'views/rfq_request.xml',
    'views/data.xml',



],
    'assets': {

    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}