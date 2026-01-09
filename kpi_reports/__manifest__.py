# -*- coding: utf-8 -*-
{
    'name': 'KPI REPORTS',
    'version': '18.0.1.0.0',
    'category': 'Reports',
    'summary': 'KPI Reports',
    'description': 'kpi',
    'depends': [
        'contacts','product','stock','purchase','stock','sale','material_purchase_requisitions',
    ],
'data': [
    'security/ir.model.access.csv',
    'views/kpi_parts_report_view.xml',
    # 'views/data.xml',



],
    'assets': {

    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}