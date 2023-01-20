# -*- coding: utf-8 -*-
{
    'name': 'Blinkers',
    'summary': 'Kits B2c1',
    'description': """This module is for Kits B2C1""",
    'author': 'Keypress IT Services',
    'version': '13.0.0.2',
    'sequence' : 1,
    'website' : 'https://www.keypress.co.in',
    'depends':['kits_multi_website'],
    'data': [
        #security
        'security/ir.model.access.csv',

        #views
        'views/kits_b2c_website.xml',
        'views/kits_b2c1_website_page_view.xml',
        'views/kits_b2c1_website_menu_view.xml',
        'views/kits_actions_views.xml',
        'views/website_templates.xml',

        
        #menuitems
        'menuitems.xml',
        
        #data
        'data/model_data.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
