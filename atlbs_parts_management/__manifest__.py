# -*- coding: utf-8 -*-
{
    'name': 'Parts',
    'version': '18.0.1.0.0',
    'category': 'Auto Parts Management',
    'summary': 'Atlabs Auto Parts Management',
    'description': 'parts',
    'depends': [
        'contacts', 'fleet','product','stock','purchase','stock','fleet','sale',
    ],
'data': [
    'security/ir.model.access.csv',
    'views/product_template.xml',
    'views/fleet_vehicle.xml',
    'views/sale_order.xml',
    'views/list_view.xml',


],
    'assets': {

    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}