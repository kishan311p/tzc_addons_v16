# -*- coding: utf-8 -*-
# Part of SnepTech See LICENSE file for full copyright and licensing details.##
##################################################################################

{
    'name': "Product Importer",
    'summary': "Import product with variant",
    'sequence':1,
    'description': "",
    'category': '',
    'version': '16.0.0.1',
    'license': 'AGPL-3',
    'author': 'SnepTech',
    'website': 'https://www.sneptech.com',
    
    'depends': ['tzc_sales_customization_spt'],

    'data': [
        'security/ir.model.access.csv',
        'data/seq.xml',
        'data/ir_server_action.xml',
        'views/product_import_spt_view.xml',
        'views/product_import_on_barcode_view.xml',
        'views/res_config_settings_view.xml',
        # 'views/stock_move_line_view.xml',
        'wizard/product_import_by_sku_wizard_view.xml',
        'wizard/kits_read_file_error_message.xml',
    ],

    'application': True,
    'installable': True,
    'auto_install': False,
    "images":['static/description/Banner.png'],
}
