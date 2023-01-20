# -*- coding: utf-8 -*-
{
    'name': 'Kits Multi Website',
    'summary': 'Kits Multi Website',
    'description': """This module is for Kits Multi Website""",
    'author': 'Keypress IT Services',
    'version': '13.0.0.2',
    'sequence' : 1,
    'website' : 'https://www.keypress.co.in',
    'depends':['stock','account','tzc_sales_customization_spt'],
    'data': [

        #security
        'security/ir.model.access.csv',
        'security/group_rule.xml',
        
        #data
        'data/sequence.xml',
        'data/ir_server_action.xml',
        'data/kits_multi_website_mail_template_data.xml',
        'data/kits_multi_website_otp_mail_template_data.xml',
        'data/kits_b2c1_sale_order_placed_email.xml',
        'data/kits_multi_website_reset_password_email.xml',
        'data/ir_cron.xml',
        'data/kits_b2c1_sale_order_prescription_email.xml',
        
        #views
        'views/kits_currency_mapping_view.xml',
        'views/kits_multi_website_sale_order_view.xml',
        'views/kits_multi_website_customer_view.xml',
        'views/kits_b2c_website_view.xml',
        'views/stock_move_view.xml',
        'views/kits_multi_website_invoice_view.xml',
        'views/kits_free_shipping_rule_view.xml',
        'views/kits_multi_website_coupon_view.xml',
        'views/kits_multi_website_coupon_customer_line_view.xml',
        'views/product_product_view.xml',
        'views/kits_multi_website_return_request_view.xml',
        'views/kits_multi_website_wallet_transaction_view.xml',
        'views/kits_multi_website_product_slider_category_view.xml',
        'views/kits_multi_website_attribute_filter_view.xml',
        'views/kits_multi_website_glass_type.xml',
        'views/kits_multi_website_power_type.xml',
        'views/kits_multi_website_lense.xml',
        'views/kits_multi_website_recent_view.xml',
        'views/kits_multi_website_wishlist.xml',
        'views/kits_multi_website_sign_up_otp_view.xml',
        'views/kits_multi_website_prescription.xml',
        'views/res_country_view.xml',
        'views/kits_multi_website_return_request_reason.xml',
        'views/kits_key_value_model.xml',
        #wizard
        'wizard/kits_multi_website_register_payment_wiz_view.xml',
        'wizard/kits_multi_website_refund_option_view.xml',
        'wizard/kits_multi_website_change_password_view.xml',
        'wizard/kits_multi_website_set_product_view.xml',
        'wizard/kits_multi_website_set_slider_category_view.xml',
        'wizard/kits_add_remove_website_wizard.xml',
        'wizard/kits_add_prescription_wizard.xml',
        'wizard/kits_multi_website_add_shipping_cost_wizard.xml',
        'wizard/kits_sale_order_line_select_wizard.xml',
        'wizard/kits_b2c_sales_report.xml',

        # #menuitems
        'menuitems.xml',

        # #report
        'reports/report_kits_b2c_sales_report_documentes.xml',
        'reports/kits_report_actions.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
