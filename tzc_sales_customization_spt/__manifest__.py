# -*- coding: utf-8 -*-
{
    'name': 'ETO Sales Customization',
    'summary': 'ETO Sales Customization',
    'description': """
    """,
    'author': 'Keypress',
    'sequence': 1,
    'version': '16.0.0',
    'depends':['base','product','stock','sale_stock','sale','sale_management','web','crm','delivery','mail','portal','mass_mailing','snailmail_account_followup','marketing_automation'],
    # 'web','website'
    'data': [
        
        # Access rules
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/security_rule.xml',
        'security/ir_rule.xml',

        # Data
        'data/ir_server_actions.xml',
        'data/report_paperformate.xml',
        'data/cron_spt.xml',
        'data/data.xml',
        'data/mail_template_customer_approve.xml',
        'data/mail_template_notify_admin_partner_country_change.xml',
        'data/pricelist.xml',
        'data/seq.xml',
        # 'data/mail_change_commission_rule_for_salesperson.xml',
        'data/mail_template_customer_approve_notify.xml',
	'data/stock_picking_mail_templates.xml',

        # Views
        'views/product_product_view.xml',
        'views/product_template_view.xml',
        'views/product_brand_view_spt.xml',
        'views/product_color_spt_view.xml',
        'views/product_model_view_spt.xml',
        'views/product_size_view_spt.xml',
        'views/product_material_spt.xml',
        'views/product_shape_view_spt.xml',
        'views/product_rim_type_view_spt.xml',
        'views/product_bridge_size_spt.xml',
        'views/product_temple_size_spt.xml',
        'views/product_aging_view_spt.xml',
        'views/product_category_view.xml',
        'views/res_config_settings_view.xml',
        'views/kits_package_product_view.xml',
        'views/geo_restriction_spt.xml',
        'views/python_script_runner_view.xml',
        'views/res_company.xml',
        'views/stock_picking_view.xml',
        'views/shipping_provider_spt_view.xml',
        'views/res_partner_view.xml',
        'views/kits_commission_rules_view.xml',
        'views/import_partner_spt_view.xml',
        'views/manage_template_view.xml',
        'views/mailgun_email_logs_view.xml',
        'views/kits_commission_lines_view.xml',
        'views/account_move_view.xml',
        'views/sale_order_view.xml',
        'views/res_users.xml',

        # Wizard
        'wizards/kits_warning_wizard_view.xml',
        'wizards/kits_bulk_discount_on_package_products_view.xml',
        'wizards/on_sale_price_wizard_spt.xml',
        'wizards/product_info_wizard_spt.xml',
        'wizards/kits_assign_salesperson_wizard_view.xml',
        'wizards/kits_change_contact_country_view.xml',
        'wizards/warning_spt_wizard_view.xml',
        'wizards/sales_commission_report_wizard_view.xml',
        'wizards/portal_users_message_wizard_spt_view.xml',
        'wizards/portal_wizard_view.xml',
        'wizards/pricelist_partner_wizard_spt_view.xml',
        'wizards/eto_partner_wizard_spt_view.xml',
        'wizards/followup_send_wizard_view.xml',
        'wizards/warning_message_wizard_view.xml',
        'wizards/kits_confirm_contact_delete_wizard_view.xml',
        'wizards/customer_from_invitation_wizard_spt_view.xml',
        'wizards/kits_customers_report_wizard_view.xml',
        'wizards/kits_replace_sales_person_wizard_view.xml',
        'wizards/kits_replace_sales_manager_wizard_view.xml',
        'wizards/kits_change_commission_rule_view.xml',
        'wizards/paid_amount_wizard_view.xml',

        # Reports
        'reports/kits_commission_report.xml',
        'reports/sales_commission_pdf_report.xml',

        # Templates
        'templates/excel_data.xml',
        


    ],

    'assets': 
    {
        'web.assets_backend': [
            'tzc_sales_customization_spt/static/src/**/*.js',
            'tzc_sales_customization_spt/static/src/**/*.scss',
        ],
        'web.assets_common': [
            'tzc_sales_customization_spt/static/src/scss/web.zoomodoo.scss',
        ],
    },

    'application': True,
    'installable': True,
    'auto_install': False,
}
