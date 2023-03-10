# -*- coding: utf-8 -*-
{
    'name': 'ETO B2B DATA',
    'summary': 'Kits B2B website',
    'description': """Kits B2B website""",
    'author': 'Keypress IT Services',
    'version': '13.0.0.1',
    'sequence' : 1,
    'website' : 'https://keypress.co.in',
    'depends':['kits_b2b_website'],
    'data': [
        # data
        'data/models_data.xml',
        'data/home_page_data.xml',
        'data/website_data.xml',
        'data/shipping_data.xml',
        'data/privacy_policy_data.xml',
        'data/terms_and_conditions_data.xml',
        'data/our_story_page.xml',
        'data/contact_us_data.xml',
        'data/menus_data.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
