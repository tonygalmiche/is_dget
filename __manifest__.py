# -*- coding: utf-8 -*-
{
    'name'     : 'InfoSaône - Module Odoo 12 pour DGET',
    'version'  : '0.1',
    'author'   : 'InfoSaône',
    'category' : 'InfoSaône',
    'description': """
InfoSaône - Module Odoo 12 pour DGET
===================================================
""",
    'maintainer' : 'InfoSaône',
    'website'    : 'http://www.infosaone.com',
    'depends'    : [
        'base',
        'base_vat',
        'sale',
        'purchase',
        'document',
        'product',
    ],
    'data' : [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/is_dossier_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'qweb': [
    ],
}

