from odoo.addons.portal.controllers.web import Home
from odoo import http, models, fields, _
from odoo.http import request
import datetime
LOC_PER_virtual_product = 45000
virtual_product_CACHE_TIME = datetime.timedelta(hours=12)
from itertools import islice
import base64

class Website(Home):

    @http.route('/virtual_product.xml', type='http', auth="public", website=True, multilang=False, sitemap=False)
    def virtual_product_xml_index(self, **kwargs):
        current_website = request.website
        Attachment = request.env['ir.attachment'].sudo()
        View = request.env['ir.ui.view'].sudo()
        mimetype = 'application/xml;charset=utf-8'
        content = None

        def create_virtual_product(url, content):
            return Attachment.create({
                'datas': base64.b64encode(content),
                'mimetype': mimetype,
                'type': 'binary',
                'name': url,
                'url': url,
            })
        dom = [('url', '=', '/virtual_product-%d.xml' % current_website.id), ('type', '=', 'binary')]
        virtual_product = Attachment.search(dom, limit=1)
        if not content:
            # Remove all virtual_products in ir.attachments as we're going to regenerated them
            dom = [('type', '=', 'binary'), '|', ('url', '=like', '/virtual_product-%d-%%.xml' % current_website.id),
                   ('url', '=', '/virtual_product-%d.xml' % current_website.id)]
            virtual_products = Attachment.search(dom)
            virtual_products.unlink()
            website_id = request.env['kits.b2c.website'].search([('website_name','=','b2c1')])
            pages = 0
            content = '<SHOP>'
            product_ids = request.env['product.product'].search([('website_ids','=',website_id.id)])
            count = 0
            for product_id in product_ids:
                count +=1
                qty = website_id.sale_pricelist_id.price_rule_get(product_id.id,1)
                content += f"""<!-- {count}-->
                                <SHOPITEM>
                                    <GROUP_ID></GROUP_ID>
                                    <ITEM_ID>{product_id.default_code}</ITEM_ID>
                                    <PRODUCTNAME><![CDATA[{product_id.display_name}]]></PRODUCTNAME>
                                    <DESCRIPTION><![CDATA[{product_id.custom_message}]]></DESCRIPTION>
                                    <PRICE>{qty[website_id.sale_pricelist_id.id][0]}</PRICE>
                                    <IMGURL>{product_id.image_url}</IMGURL>
                                    <URL>{website_id.url}/product/{product_id.product_seo_keyword}</URL>
                                    <CATEGORY>{16 if product_id.categ_id.name == 'E' else 11}</CATEGORY>
                                    <SEX>{'W' if product_id.gender == 'female' else 'M' if product_id.gender == 'male' else 'U'}</SEX>
                                    <EAN></EAN>
                                    <MANUFACTURER><![CDATA[{product_id.brand.name}]]></MANUFACTURER>
                            </SHOPITEM>"""
            content +='</SHOP>'
            content=content.replace(';', "\n")
            content = View.render_template('kits_b2c1.virtual_product_xml', {'content': content})
            pages += 1
            last_virtual_product = create_virtual_product('/virtual_product-%d-%d.xml' % (current_website.id, pages), content)

            if not pages:
                return request.not_found()
            elif pages == 1:
                # rename the -id-page.xml => -id.xml
                last_virtual_product.write({
                    'url': "/virtual_product-%d.xml" % current_website.id,
                    'name': "/virtual_product-%d.xml" % current_website.id,
                })
            else:
                # TODO: in master/saas-15, move current_website_id in template directly
                pages_with_website = ["%d-%d" % (current_website.id, p) for p in range(1, pages + 1)]

                # virtual_products must be split in several smaller files with a virtual_product index
                content = View.render_template('kits_b2c1.virtual_product_index_xml', {
                    'pages': pages_with_website,
                    'url_root': request.httprequest.url_root,
                })
                create_virtual_product('/virtual_product-%d.xml' % current_website.id, content)

        return request.make_response(content, [('Content-Type', mimetype)])
