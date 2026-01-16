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
    'report/kpi_parts_pdf.xml',
    'views/kpi_parts_report_view.xml',
    'wizard/kpi_parts_detailed_wizard.xml',
    # 'views/data.xml',



],
    'assets': {
        'web.assets_backend': [
        # 'kpi_reports/static/src/css/list_view.css',
        # 'kpi_reports/static/src/js/list_views.js',
    ],

    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}