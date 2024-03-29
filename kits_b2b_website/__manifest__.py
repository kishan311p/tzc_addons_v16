# -*- coding: utf-8 -*-
{
    'name': 'ETO B2B',
    'summary': 'Kits B2B website',
    'description': """Kits B2B website""",
    'author': 'Keypress IT Services',
    'version': '13.0.0.1',
    'license':'LGPL-3',
    'sequence' : 1,
    'website' : 'https://keypress.co.in',
    'depends':['tzc_sales_customization_spt'],
    'data': [
        # data
        'data/mail_template_b2b_reset_password_email.xml',
        'data/mail_template.xml',
        'data/website_data.xml',
        
        #security
        'security/ir.model.access.csv',

        #views
        'views/kits_b2b_website.xml',
        'views/kits_b2b_website_slider.xml',
        'views/kits_b2b_pages.xml',
        'views/kits_b2b_menus.xml',
        'views/kits_b2b_image_model.xml',
        'views/kits_b2b_key_value_model.xml',
        'views/kits_b2b_user_token.xml',
        'views/kits_b2b_multi_currency_mapping.xml',
        'views/kits_b2b_product_wishlist.xml',
        'views/kits_b2b_recent_view.xml',
        'views/res_users.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/kits_landing_view.xml',
        'views/kits_special_discount_offers_view.xml',
        #actions
        'action.xml',
        'menuitem.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
