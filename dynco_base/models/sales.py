# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

import numpy as np
import datetime
import pytz
import base64
import io
import os
import pyqrcode
import sys
import traceback
from PIL import Image
from pytz import timezone
import requests
import json
import logging

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import mod10r
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang
from odoo.http import request

_logger = logging.getLogger(__name__)

CH_KREUZ_IMAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "src", "img", "CH-Kreuz_7mm.png")
IBAN_LENGTH_NO_CHECK_DIGIT = 26


class ProviderGrid(models.Model):
    _inherit = 'delivery.carrier'

    def base_on_rule_rate_shipment(self, order):
        carrier = self._match_address(order.partner_shipping_id)
        if not carrier:
            return {'success': False,
                    'price': 0.0,
                    'error_message': _('Error: this delivery method is not available for this address.'),
                    'warning_message': False}

        try:
            price_unit = self._get_price_available(order)
        except UserError as e:
            return {'success': False,
                    'price': 0.0,
                    'error_message': e.args[0],
                    'warning_message': False}
        #exclude currency conversion for delivery price
        #price_unit = self._compute_currency(order, price_unit, 'company_to_pricelist')

        return {'success': True,
                'price': price_unit,
                'error_message': False,
                'warning_message': False}


class SaleStage(models.Model):
    _name = "sale.stage"
    _description = "Sale Stages"
    _rec_name = 'name'
    _order = "sequence, name, id"

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    fold = fields.Boolean('Folded in kanban', help='This stage is folded in the kanban view when there are no records in that stage to display.')


class SaleOrder(models.Model):
    _inherit = "sale.order"

    amount_handling = fields.Monetary(
        compute='_compute_amount_handling',
        string='Handling Amount',
        help="The amount without tax.", store=True, tracking=True)

    @api.depends('order_line.price_unit', 'order_line.tax_id', 'order_line.discount', 'order_line.product_uom_qty')
    def _compute_amount_delivery(self):
        for order in self:
            if self.env.user.has_group('account.group_show_line_subtotals_tax_excluded'):
                order.amount_delivery = sum(order.order_line.filtered(lambda line: line.is_delivery and not line.is_handling).mapped('price_subtotal'))
            else:
                order.amount_delivery = sum(order.order_line.filtered(lambda line: line.is_delivery and not line.is_handling).mapped('price_total'))

    @api.depends('order_line.price_unit', 'order_line.tax_id', 'order_line.discount', 'order_line.product_uom_qty')
    def _compute_amount_handling(self):
        for order in self:
            if self.env.user.has_group('account.group_show_line_subtotals_tax_excluded'):
                order.amount_handling = sum(order.order_line.filtered('is_handling').mapped('price_subtotal'))
            else:
                order.amount_handling = sum(order.order_line.filtered('is_handling').mapped('price_total'))

    def _default_stage_id(self):
        return self.env['sale.stage'].search([('fold', '=', False)], limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return self.env['sale.stage'].search([], order=order)

    stage_id = fields.Many2one('sale.stage', string='Stage', ondelete='restrict', tracking=True, index=True, default=lambda self: self._default_stage_id(), group_expand='_read_group_stage_ids')
    delivery_detail = fields.Char(string="Delivery Order", compute='_so_delivery', store=True)
    vendors_ids = fields.Many2many(
        'res.partner', compute='_get_product_vendors')
    vendor = fields.Many2one(
        'res.partner', string='Vendor',
        domain="[('id', 'in', vendors_ids)]")
    is_delivered = fields.Boolean(string="Is Delivered", default=False, copy=False)
    margin_after_transport = fields.Monetary(string="Margin AT", track_visibility='onchange', copy=False)
    margin_after_transpor_per = fields.Float(string="Margin AT %", track_visibility='onchange', copy=False)
    transport_cost = fields.Float(string="Transport Cost", track_visibility='onchange', copy=False)
    actual_delivery_date = fields.Datetime(string='Actual Delivery Date', help="Date on which the order is ship.", copy=False, track_visibility='onchange')
    schedule_date = fields.Datetime(string='Schedule Date', help="Date on which the order is schedule.", copy=False, track_visibility='onchange')
    state = fields.Selection(selection_add=[('delivered', 'Delivered'), ('complete', 'Complete')])
    days_of_develiry = fields.Integer(string="Days of Delivery", copy=False)

    partner_bank_id = fields.Many2one('res.partner.bank', string='Bank Account', domain=lambda self: [('partner_id', '=', self.env.user.company_id.partner_id.id)])
    bvr_reference = fields.Text(string='Additional Information')
    qr_reference = fields.Char(string='QR reference', compute='_create_qr_reference', store=True)
    qrcode_qrbill = fields.Binary(string='QRCode', compute='_iban_qrcode', store=False)
    qrcode_status = fields.Text(string='QRCode Status', compute='_iban_qrcode', store=False)
    account_holder_id = fields.Many2one(related='partner_bank_id.partner_id', store=True)
    invoice_date = fields.Date(compute="_compute_invoice_date", store=True)
    expected_date = fields.Datetime("Expected Date", compute='_compute_expected_date', store=True,
        help="Delivery date you can promise to the customer, computed from the minimum lead time of the order lines.")
    free_delivery_message = fields.Html("Check free delivery message", translate=True)
    show_note_warning = fields.Boolean(compute="_compute_note", string='Show Note Warning')

    @api.depends("note")
    def _compute_note(self):
        default_value = '<p><br></p>'
        if self.note == default_value:
            self.show_note_warning = False
        elif self.note:
            self.show_note_warning = True
        else:
            self.show_note_warning = False


    @api.depends('order_line.customer_lead', 'date_order', 'order_line.state')
    def _compute_expected_date(self):
        return super()._compute_expected_date()

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        brand = self.partner_id.b2b_delivery_method_id.filtered(lambda x: x.brand_id == self.brand_id)
        if brand and brand.delivery_id:
            delivery_message = ''
            vals = brand.delivery_id.rate_shipment(self)
            delivery_message = ''
            if vals.get('success'):
                delivery_message = vals.get('warning_message', False)
            if delivery_message:
                vals['free_delivery_message'] = delivery_message
            else:
                price = sum(self.order_line.filtered(lambda line: not line.display_type).mapped('price_subtotal'))
                new_price = brand.delivery_id.amount - price
                data = _("Free Delivery from:")+"<strong>"+(formatLang(self.env, brand.delivery_id.amount, currency_obj=self.env.company.currency_id).replace(u'\xa0', ' '))+"</strong><br/>"+_("To add for free delivery:") + "<strong>"+(formatLang(self.env, new_price, currency_obj=self.env.company.currency_id).replace(u'\xa0', ' '))+ "</strong>"
                vals['free_delivery_message'] = data

        for record in self:
            if res and record.state in ['sale', 'done']:
                record.send_post_request()
        return res

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        if order.state in ['sale', 'done']:
            order.send_post_request()
        return order

    @api.model
    def send_post_request(self):
        url = False
        if self.website_id.webhook_url:
            url = self.website_id.webhook_url
        # url = 'https://app.trueroas.io/api/other/ordercreated?uid=u6wWow0qsMcRgE9ZsrP5Uvu4kUw2&pixel_id=www.climaqua.com'
        if self and url:
            environ = request.httprequest.headers.environ
            IP_ADDRESS = environ.get("REMOTE_ADDR")
            HTTP_USER_AGENT = environ.get("HTTP_USER_AGENT")
            HTTP_REFERER = environ.get("HTTP_REFERER")
            order = self
            payload = {
                'order_id': str(order.id),
                'date_created': order.create_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'date_updated': order.write_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'timezone': 'UTC',
                'customer_id': str(order.partner_id.id),
                'discount_codes': [{}],
                # 'discount_codes': [{'code': discount.code} for discount in order.discount_ids],
                'products': [{
                    'sku': line.product_id.default_code,
                    'product_id': str(line.product_id.id),
                    'name': line.product_id.name,
                    'variant_id': str(line.product_id.product_variant_id.id),
                    'variant_title': line.product_id.product_variant_id.name,
                    'image_url': line.product_id.product_img_url or '',
                    'quantity': line.product_uom_qty,
                    'shop_money': {
                        'currency_code': order.currency_id.name,
                        'amount': line.price_subtotal
                    }
                } for line in order.order_line],
                'currency': order.currency_id.name,
                'total_price': order.amount_total,
                'total_tax': order.amount_tax,
                'total_shipping': order.amount_delivery,
                'email': order.partner_id.email,
                'customer_ip_address': str(IP_ADDRESS),
                'locationHref': str(HTTP_REFERER),
                'user_agent': str(HTTP_USER_AGENT),
                # 'cost_of_goods': sum(line.cost_price * line.product_uom_qty for line in order.order_line),
                'cost_of_goods': order.tax_totals_json,
                'shipping_cost': order.amount_delivery,
            }

            json_payload = json.dumps(payload)

            headers = {'Content-Type': 'application/json'}

            response = requests.post(url, data=json_payload, headers=headers)
            if response.status_code == 200:
                _logger.info('POST request successful: %s', response.text)
                # try:
                #     response_data = response.json()
                #     _logger.info('POST request successful: %s', response_data)
                # except json.JSONDecodeError:
                #     _logger.error('Failed to decode JSON response. Response text: %s', response.text)
            else:
                _logger.error('Failed to send POST request. Status code: %s, Response text: %s', response.status_code, response.text)

        return True

    @api.depends("invoice_status")
    def _compute_invoice_date(self):
        for order in self:
            if order.invoice_ids:
                order.invoice_date = order.invoice_ids[-1].invoice_date
            else:
                order.invoice_date = False

    def knk_print_ch_qr_code(self):
        """ Triggered by the 'Print QR-bill' button.
        """
        self.ensure_one()
        return self.env.ref('dynco_base.action_print_qrsaleorder').report_action(self)

    @api.onchange('partner_id', 'currency_id')
    def onchange_partner_bank_id(self):
        company = self.env.user.company_id
        if self.partner_id and self.partner_id.preferred_bank_id:
            self.partner_bank_id = self.partner_id.preferred_bank_id.id
        else:
            if self.currency_id:
                bank = self.env['res.partner.bank'].search([('partner_id', '=', company.partner_id.id), ('currency_id', '=', self.currency_id.id)], limit=1)
                self.partner_bank_id = bank.id

    @api.model
    @api.depends('name', 'partner_bank_id.invoice_issuer_number')
    def _create_qr_reference(self):
        for order in self:
            qr_reference = ''

            if order.partner_bank_id:
                invoice_issuer_number = order.partner_bank_id.invoice_issuer_number
                order_number = ''

                try:
                    if order.name:
                        for letter in order.name:
                            if letter.isdigit():
                                order_number += letter
                except:
                    None

                if order_number:
                    order_internal_ref = order_number

                    if invoice_issuer_number and invoice_issuer_number.isdigit():

                        qr_reference = invoice_issuer_number + order_internal_ref.rjust(IBAN_LENGTH_NO_CHECK_DIGIT - len(invoice_issuer_number), '0')

                    else:
                        qr_reference = order_internal_ref.rjust(IBAN_LENGTH_NO_CHECK_DIGIT, '0')

                    order.qr_reference = mod10r(qr_reference)

    @api.model
    def _iban_qrcode(self):
        for order in self:
            order.qrcode_qrbill = False
            order.qrcode_status = False
            try:
                if order.name:
                    order.qrcode_qrbill = self._generate_qrbill_base64(order)
                else:
                    self._generate_qrbill_content(order)
                    order.qrcode_status = _("The QRCode will be generated once you validate the Order")
            except Exception as orm_ex:
                order.qrcode_status = "%s" % (orm_ex)
            except Exception as ex:
                traceback.print_exc(file=sys.stdout)
                order.qrcode_status = str(ex)

    def _generate_qrbill_base64(self, order):
        qr_content = self._generate_qrbill_content(order)
        qr = pyqrcode.create(qr_content, error='M', encoding='utf-8')
        # import pdb;pdb.set_trace()

        with io.BytesIO() as f:
            # import pdb;pdb.set_trace()
            qr.png(f, scale=7, module_color=(0, 0, 0, 255), background=(255, 255, 255, 255), quiet_zone=0)

            f.seek(0)

            with Image.open(f) as im:
                with Image.open(CH_KREUZ_IMAGE_PATH) as original_logo:
                    logo = original_logo.resize((75, 75))

                with logo:
                    start_x = int((im.width - logo.width) / 2)
                    start_y = int((im.height - logo.height) / 2)
                    box = (start_x, start_y, start_x + logo.width, start_y + logo.height)
                    im.paste(logo, box)

                f.seek(0)
                im.save(f, format='PNG')
            f.seek(0)
            b64_qr = base64.b64encode(f.read())

        return b64_qr

    def _generate_qrbill_content(self, order):
        qr_type = 'SPC'
        version = '0200'
        coding_type = '1'

        if not order.partner_bank_id:
            raise UserError(_('Invalid IBAN \n You must specify an IBAN'))
        creditor_iban = order.partner_bank_id.sanitized_acc_number
        if (not isinstance(creditor_iban, str)) or (len(creditor_iban) == 0):
            raise UserError(_('Invalid IBAN \n You must specify an IBAN'))
        elif not (creditor_iban.startswith("CH") or creditor_iban.startswith("LI")):
            raise UserError(_('Invalid IBAN \n Only IBANs starting with CH or LI are permitted.'))
        elif not len(creditor_iban) == 21:
            raise UserError(_('Invalid IBAN \n IBAN length must be exactly 21 characters long'))

        creditor = self._generate_qrbill_contact_data(order.company_id.partner_id, "Creditor")

        ultimate_creditor = '\r\n\r\n\r\n\r\n\r\n\r\n\r'

        total_amount = "%0.2f" % order.amount_total

        currency = order.currency_id.name
        if currency not in ["CHF", "EUR"]:
            raise UserError(_('Invalid Currency \n Currency must be either CHF or EUR'))

        ultimate_debtor = self._generate_qrbill_contact_data(order.partner_id, "Debtor")

        ref_type = 'NON'
        ref = '\r'
        if hasattr(order, 'qr_reference') and isinstance(order.qr_reference, str):
            tmp_ref = order.qr_reference.replace(' ', '')
            if tmp_ref and len(tmp_ref) > 0:
                ref_type = 'QRR'
                ref = tmp_ref
                if not len(ref) == 27:
                    raise UserError(_('Invalid BVR Reference Number \n BVR reference number length must be exactly 27 characters long'))

        unstructured_message = '\r'

        trailer = 'EPD'

        bill_information = '\r'

        alternative_scheme_1 = '\r'
        alternative_scheme_2 = '\r'

        return '\n'.join([
            qr_type,
            version,
            coding_type,
            creditor_iban,
            creditor,
            ultimate_creditor,
            total_amount,
            currency,
            ultimate_debtor,
            ref_type,
            ref,
            unstructured_message,
            trailer,
            bill_information,
            alternative_scheme_1,
            alternative_scheme_2
            ])

    def _generate_qrbill_contact_data(self, contact, role):
        if not contact:
            raise UserError(_('Invalid ' + role, role + ' is mandatory'))

        if (not contact.is_company) and contact.parent_id.name:
            contact_name = contact.parent_id.name
        else:
            contact_name = contact.name
        if not contact_name or len(contact_name) == 0:
            raise UserError(_("Invalid " + role + "'s Name", role + "'s name is mandatory"))
        elif len(contact_name) > 70:
            raise UserError(_("Invalid " + role + "'s Name", role + "'s name length must not exceed 70 characters"))

        contact_street_and_nb = contact.street
        if not contact_street_and_nb or len(contact_street_and_nb) == 0:
            contact_street_and_nb = "\r"
        elif len(contact_street_and_nb) > 70:
            raise UserError(_("Invalid " + role + "'s Street", role + "'s street length must not exceed 70 characters"))

        contact_postal_code = contact.zip
        if not contact_postal_code or len(contact_postal_code) == 0:
            raise UserError(_('Invalid ' + role + '\'s Postal Code', role + '\'s postal code is mandatory'))

        contact_city = contact.city
        if not contact_city or len(contact_city) == 0:
            raise UserError(_('Invalid ' + role + '\'s City', role + '\'s city is mandatory'))

        contact_zip_and_city = contact_postal_code + ' ' + contact_city
        if len(contact_zip_and_city) > 70:
            raise UserError(_('Invalid ' + role + '\'s City', role + '\'s city length must not exceeds 70 characters'))

        contact_country = contact.country_id.code
        if not contact_country or len(contact_country) == 0:
            raise UserError(_('Invalid ' + role + '\'s Country Code', role + '\'s country code is mandatory'))
        if not len(contact_country) == 2:
            raise UserError(_('Invalid ' + role + '\'s Country Code', role + '\'s country code length must be exactly 2 characters long.'))

        return '\n'.join([
            'K',
            contact_name,
            contact_street_and_nb,
            contact_zip_and_city,
            '\r',
            '\r',
            contact_country
            ])

    # already available fields
    # margin_percent = fields.Float(
    #     string='Margin %', compute='_product_margin_percentage')

    @api.depends('picking_ids')
    def _so_delivery(self):
        for order in self:
            order.delivery_detail = ','.join([p.name for p in order.picking_ids])

    # already available fields
    # @api.depends('order_line')
    # def _product_margin_percentage(self):
    #     for order in self:
    #         if order.order_line and order.amount_untaxed > 0:
    #             order.margin_percent = (order.margin / order.amount_untaxed) * 100

    @api.depends('order_line.product_id')
    def _get_product_vendors(self):
        vendors = []
        for line in self.order_line:
            seller = self.env['product.supplierinfo']
            if line.order_id.website_id.name == 'lechuza.dynco.spt':
                seller = line.product_id.seller_ids.filtered(lambda x: x.name.id == line.order_id.partner_id.id)[:1]
            elif line.order_id.partner_id.business_type == 'b2b' and 'Geobra Brandstätter Stiftung & Co. KG' in line.product_id.seller_ids.mapped('name.name'):
                seller = line.product_id.seller_ids.filtered(lambda x: x.cost_price != 0.0 and x.name.name == 'Geobra Brandstätter Stiftung & Co. KG')[:1]
            elif line.order_id.partner_id.business_type == 'b2c' and 'Blumenbörse Rothrist' in line.product_id.seller_ids.mapped('name.name'):
                seller = line.product_id.seller_ids.filtered(lambda x: x.cost_price != 0.0 and x.name.name == 'Blumenbörse Rothrist')[:1]
            else:
                seller = line.product_id.seller_ids[:1] if line.product_id.seller_ids[:1] else seller
            if seller.name:
                vendors.append(seller.name.id)
        self.vendors_ids = vendors

    def _get_formated_amount(self, amount):
        self.ensure_one()
        res = formatLang(self.env, amount, currency_obj=None)
        res = res.replace("CHF", "")
        return res

    def action_update_margin(self):
        for line in self.order_line:
            line._compute_purchase_price()
            line._compute_margin()

    def action_view_sale_delivery_lead(self):
        product_brand = any(line.product_id.product_brand_lead for line in self.order_line)
        picking_state = any(picking.state == 'done' for picking in self.picking_ids)
        if not picking_state:
            raise ValidationError(_('You can not Set Delivered this Order without Delivery Done.'))
        if not product_brand:
            raise ValidationError(_('You need to set the Brand on Product'))
        ctx = self.env.context.copy()
        ctx.update({'default_is_delivered_wizard': self.is_delivered})
        return {
            'name': _('Sales Delivery Lead Advance'),
            'type': 'ir.actions.act_window',
            # 'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.delivery.lead.advance',
            'target': 'new',
            'context': ctx
        }

    def action_delivered(self, date, tc):
        ''' Set the difference day(s) count with schedule and actual delivery order. '''
        for order in self:
            holidays = []
            if not order.invoice_ids:
                raise ValidationError(_('There is no Invoice for "%s" Order.! You can not Delivered this Order. \n First Create the Invoice for this Order After that Process to Delivered.') % order.name)
            if not order.is_delivered:
                order.actual_delivery_date = date
                public_holiday = self.env['resource.calendar.leaves'].search([])
                for global_leave in public_holiday:
                    holidays.append(datetime.datetime.strftime(global_leave.date_from, "%Y-%m-%d"))
                # subscract the day(s) with check weekends and holidays
                days = np.busday_count(order.actual_delivery_date.date(), order.schedule_date.date(), holidays=holidays)
                diff_days = -(days) - 1 if days > 0 else -(days)
                order.write({'days_of_develiry': diff_days, 'is_delivered': True, 'state': 'delivered'})
                purchase_order = self.env['purchase.order'].search([('group_id', '=', order.procurement_group_id.id)])
                if purchase_order:
                    purchase_order.write({'days_of_develiry': order.days_of_develiry})
            else:
                order.write({'transport_cost': tc,
                            'margin_after_transport': order.margin - tc,
                            'margin_after_transpor_per': (order.margin - tc) / order.amount_untaxed * 100 if order.amount_untaxed > 0 else 1,
                            'state': 'complete'
                            })

    def action_confirm(self):
        product_brand = []
        lead_data = []
        holidays = []
        res = super(SaleOrder, self).action_confirm()
        for line in self.order_line:
            for product in line.product_id:
                product_brand.append(product.product_brand_lead)
        # If Customer have not set brand lead time than take from default company setting.
        if not self.partner_id.product_brand_lead_ids:
            product_brand_lead_data = self.company_id.comp_product_brand_lead_ids
        else:
            product_brand_lead_data = self.partner_id.product_brand_lead_ids
        for brand_lead in product_brand_lead_data:
            if brand_lead.product_brand_lead not in product_brand:
                continue
            lead_data.append(brand_lead.delivery_lead_time)

        if lead_data:
            max_lead = max(lead_data)
            public_holiday = self.env['company.resource.calendar'].search([])
            for global_leave in public_holiday.mapped('company_global_leave_ids'):
                holidays.append(datetime.datetime.strftime(global_leave.date_from, "%Y-%m-%d"))
            dateorder = datetime.datetime.now().strptime(datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),DEFAULT_SERVER_DATETIME_FORMAT)
            self.schedule_date = self.date_by_adding_business_days(dateorder, max_lead, holidays)
        return res

    def date_by_adding_business_days(self, from_date, add_days, holidays):
        '''
        Check the Only WeekDay from the register: Confirmation Date
        Return : Exclue Weekend day + Holiday's Calcualte Date
        '''
        business_days_to_add = add_days - 1
        current_date = from_date
        def utc_time_convert(current_date):
            count = 0
            user_tz = self.env.user.tz or 'UTC'
            local = pytz.timezone(user_tz)
            current_date = datetime.datetime.strptime(
                datetime.datetime.strftime(
                    timezone('UTC').localize(
                        datetime.datetime.strptime(
                            str(current_date),
                            DEFAULT_SERVER_DATETIME_FORMAT)
                        ).astimezone(local), "%d/%m/%Y %H:%M:%S"), '%d/%m/%Y %H:%M:%S')
            if current_date.time() < datetime.time(12):
                count = 1
            return count

        while business_days_to_add >= utc_time_convert(current_date):
            current_date += datetime.timedelta(days=1)
            weekday = current_date.weekday()
            if weekday >= 5:
                continue
            if datetime.datetime.strftime(current_date, "%Y-%m-%d") in holidays:
                continue
            business_days_to_add -= 1
        return current_date

    @api.model
    def auto_cancel_quotation(self):
        dt = datetime.datetime.today() - datetime.timedelta(days=10)
        orders = self.search([('state', 'in', ['draft', 'sent']), ('team_id.team_type', '=', 'website'), ('create_date', '<=', dt)])
        for order in orders:
            if order.website_id and order.partner_id.business_type == 'b2c':
                order.action_cancel()

    def _create_delivery_line(self, carrier, price_unit):
        res = super()._create_delivery_line(carrier=carrier, price_unit=price_unit)
        if carrier.is_handling_charge and carrier.handling_amount_limit > sum(self.order_line.filtered(lambda x: not x.is_delivery).mapped('price_total')):
            SaleOrderLine = self.env['sale.order.line']
            context = {}
            if self.partner_id:
                # set delivery detail in the customer language
                context['lang'] = self.partner_id.lang
                carrier = carrier.with_context(lang=self.partner_id.lang)

            # Apply fiscal position
            handling_taxes = carrier.product_id.taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)
            handling_taxes_ids = handling_taxes.ids
            if self.partner_id and self.fiscal_position_id:
                handling_taxes_ids = self.fiscal_position_id.map_tax(handling_taxes).ids

            # Create the sales order line

            if carrier.handling_product_id.description_sale:
                handling_so_description = '%s: %s' % (carrier.name, carrier.handling_product_id.description_sale)
            else:
                handling_so_description = carrier.name
            values = {
                'order_id': self.id,
                'name': handling_so_description,
                'product_uom_qty': 1,
                'product_uom': carrier.handling_product_id.uom_id.id,
                'product_id': carrier.handling_product_id.id,
                'tax_id': [(6, 0, handling_taxes_ids)],
                'is_delivery': True,
                'is_handling': True,
                'price_unit': carrier.handling_charges,
            }
            if self.order_line:
                values['sequence'] = self.order_line[-1].sequence + 1
            SaleOrderLine.sudo().create(values)
            del context
        return res

    def _website_product_id_change(self, order_id, product_id, qty=0, **kwargs):
        order = self.sudo().browse(order_id)
        product_context = dict(self.env.context)
        product_context.setdefault('lang', order.partner_id.lang)
        product_context.update({
            'partner': order.partner_id,
            'quantity': qty,
            'date': order.date_order,
            'pricelist': order.pricelist_id.id,
        })
        product = self.env['product.product'].with_context(product_context).with_company(order.company_id.id).browse(product_id)
        discount = 0

        if order.pricelist_id.discount_policy == 'without_discount':
            # This part is pretty much a copy-paste of the method '_onchange_discount' of
            # 'sale.order.line'.
            price, rule_id = order.pricelist_id.with_context(product_context).get_product_price_rule(product, qty or 1.0, order.partner_id)
            pu, currency = request.env['sale.order.line'].with_context(product_context)._get_real_price_currency(product, rule_id, qty, product.uom_id, order.pricelist_id.id)
            if rule_id:
                c_rule_id = self.env['product.pricelist.item'].browse(rule_id)
                if c_rule_id.md_fixed_price:
                    pu = c_rule_id.md_fixed_price

            if order.pricelist_id and order.partner_id:
                order_line = order._cart_find_product_line(product.id)
                if order_line:
                    price = product._get_tax_included_unit_price(
                        self.company_id,
                        order.currency_id,
                        order.date_order,
                        'sale',
                        fiscal_position=order.fiscal_position_id,
                        product_price_unit=price,
                        product_currency=order.currency_id
                    )
                    pu = product._get_tax_included_unit_price(
                        self.company_id,
                        order.currency_id,
                        order.date_order,
                        'sale',
                        fiscal_position=order.fiscal_position_id,
                        product_price_unit=pu,
                        product_currency=order.currency_id
                    )
            if pu != 0:
                if order.pricelist_id.currency_id != currency:
                    # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                    date = order.date_order or fields.Date.today()
                    pu = currency._convert(pu, order.pricelist_id.currency_id, order.company_id, date)
                discount = (pu - price) / pu * 100
                if discount < 0:
                    # In case the discount is negative, we don't want to show it to the customer,
                    # but we still want to use the price defined on the pricelist
                    discount = 0
                    pu = price
            else:
                # In case the price_unit equal 0 and therefore not able to calculate the discount,
                # we fallback on the price defined on the pricelist.
                pu = price
        else:
            pu = product.price
            if order.pricelist_id and order.partner_id:
                order_line = order._cart_find_product_line(product.id, force_search=True)
                if order_line:
                    pu = product._get_tax_included_unit_price(
                        self.company_id,
                        order.currency_id,
                        order.date_order,
                        'sale',
                        fiscal_position=order.fiscal_position_id,
                        product_price_unit=product.price,
                        product_currency=order.currency_id
                    )

        return {
            'product_id': product_id,
            'product_uom_qty': qty,
            'order_id': order_id,
            'product_uom': product.uom_id.id,
            'price_unit': pu,
            'discount': discount,
        }


class SaleReport(models.Model):
    _inherit = 'sale.report'

    l_margin_percent = fields.Float(
        string='Margin %', group_operator="avg")

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['l_margin_percent'] = ", SUM(l.margin / (CASE COALESCE(l.price_subtotal, 0) WHEN 0 THEN 1.0 ELSE l.price_subtotal END) * 100) AS l_margin_percent"
        groupby += ', l.margin_percent'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    delivered_price_subtotal = fields.Monetary(compute='_delivered_price_subtotal', string='Delivered Total', readonly=True, store=True)
    invoiced_price_subtotal = fields.Monetary(compute='_invoiced_price_subtotal', string='Invoiced Total', readonly=True, store=True)
    sd_on_hand = fields.Html(related='product_id.curr_location', string="Available")
    is_handling = fields.Boolean(string="Is Handling")

    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        brand = self.order_id.partner_id.b2b_delivery_method_id.filtered(lambda x: x.brand_id == self.order_id.brand_id)
        if brand and brand.delivery_id:
            delivery_message = ''
            vals = brand.delivery_id.rate_shipment(self.order_id)
            delivery_message = ''
            if vals.get('success'):
                delivery_message = vals.get('warning_message', False)
            if delivery_message:
                self.order_id.free_delivery_message = delivery_message
            else:
                price = sum(self.order_id.order_line.filtered(lambda line: not line.display_type).mapped('price_subtotal'))
                new_price = brand.delivery_id.amount - price
                data = _("Free Delivery from:")+"<strong>&nbsp;"+(formatLang(self.env, brand.delivery_id.amount, currency_obj=self.env.company.currency_id).replace(u'\xa0', ' '))+"</strong><br/>"+_("To add for free delivery:") + "<strong>&nbsp;"+(formatLang(self.env, new_price, currency_obj=self.env.company.currency_id).replace(u'\xa0', ' '))+ "</strong>"
                self.order_id.free_delivery_message = data
        return res

    @api.depends('qty_delivered', 'discount', 'price_unit', 'tax_id')
    def _invoiced_price_subtotal(self):
        for line in self:
            qty = line.qty_invoiced if line.product_id.type in ['consu', 'product'] else line.product_uom_qty
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'invoiced_price_subtotal': taxes['total_excluded'],
            })

    @api.depends('qty_delivered', 'discount', 'price_unit', 'tax_id')
    def _delivered_price_subtotal(self):
        for line in self:
            qty = line.qty_delivered if line.product_id.type in ['consu', 'product'] else line.product_uom_qty
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'delivered_price_subtotal': taxes['total_excluded'],
            })

    @api.depends('product_id', 'company_id', 'currency_id', 'product_uom', 'product_id.seller_ids', 'order_id.partner_id.business_type')
    def _compute_purchase_price(self):
        for line in self:
            if not line.product_id:
                line.purchase_price = 0.0
                continue
            line = line.with_company(line.company_id)
            product_cost = line.product_id.standard_price
            line.purchase_price = line._convert_price(product_cost, line.product_id.uom_id)
            price = line._convert_price(product_cost, line.product_id.uom_id)
            # Custom Logic For Dynco
            if line.order_id.partner_id.business_type in ['b2b', False] and 29960 in line.product_id.seller_ids.mapped('name').ids:
                price = line.product_id.seller_ids.filtered(lambda x: x.cost_price != 0.0 and x.name.id == 29960).sorted('sequence', reverse=True)[:1].cost_price
            elif line.order_id.partner_id.business_type == 'b2c' and 29642 in line.product_id.seller_ids.mapped('name').ids:
                price = line.product_id.seller_ids.filtered(lambda x: x.cost_price != 0.0 and x.name.id == 29642).sorted('sequence', reverse=True)[:1].cost_price
            else:
                price = line.product_id.seller_ids.sorted('sequence', reverse=True)[:1].cost_price if line.product_id.seller_ids.sorted('sequence', reverse=True)[:1] else 0.0
            line.purchase_price = price

    @api.depends('price_subtotal', 'product_uom_qty', 'purchase_price')
    def _compute_margin(self):
        for line in self:
            line.margin = line.price_subtotal - (line.purchase_price * line.product_uom_qty)
            line.margin_percent = line.price_subtotal and line.margin/line.price_subtotal
            # Custom Logic For Dynco
            if line.price_unit > 0.0 and line.purchase_price > 0.0:
                line.margin_percent = ((line.price_unit - line.purchase_price) / line.price_unit)

#     @api.depends('margin')
#     def _product_l_margin_percentage(self):
#         for line in self:
#             if line.price_subtotal > 0.0:
#                 line.l_margin_percent = (line.margin/line.price_subtotal) * 100

#     l_margin_percent = fields.Float(
#         string='Margin %', compute='_product_l_margin_percentage', store=True)
#     knk_purchase_price = fields.Float(string='Cost', digits='Product Price', compute='_product_margin', store=True)

#     @api.depends('product_id', 'purchase_price', 'product_uom_qty', 'price_unit',
#                  'price_subtotal', 'order_id.vendor', 'product_id.seller_ids', 'order_id.partner_id.business_type')
#     def _product_margin(self):
#         for line in self:
#             currency = line.order_id.pricelist_id.currency_id
#             if line.order_id.vendor:
#                 if line.product_id.seller_ids:
#                     for seller in line.product_id.seller_ids:
#                         if seller.name.id == line.order_id.vendor.id:
#                             price = seller.cost_price
#                             break
#                         else:
#                             price = line.purchase_price
#                 else:
#                     price = line.purchase_price
#             if line.order_id.website_id.name == 'lechuza.dynco.spt':
#                 price = line.product_id.seller_ids.filtered(lambda x: x.name.id == line.order_id.partner_id.id)[:1].cost_price
#             elif line.order_id.partner_id.business_type == 'b2b' and 'Geobra Brandstätter Stiftung & Co. KG' in line.product_id.seller_ids.mapped('name.name'):
#                 price = line.product_id.seller_ids.filtered(lambda x: x.cost_price != 0.0 and x.name.name == 'Geobra Brandstätter Stiftung & Co. KG')[:1].cost_price
#             elif line.order_id.partner_id.business_type == 'b2c' and 'Blumenbörse Rothrist' in line.product_id.seller_ids.mapped('name.name'):
#                 price = line.product_id.seller_ids.filtered(lambda x: x.cost_price != 0.0 and x.name.name == 'Blumenbörse Rothrist')[:1].cost_price
#             else:
#                 price = line.product_id.seller_ids[:1].cost_price if line.product_id.seller_ids[:1] else 0.0
#             line.knk_purchase_price = price
#             line.margin = currency.round(
#                 line.price_subtotal - (price * line.product_uom_qty))


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    handling_product_id = fields.Many2one('product.product', string="Handling Product")
    handling_charges = fields.Float(string="Handling Charges")
    is_handling_charge = fields.Boolean(string="Chargable if the order aount is below")
    handling_amount_limit = fields.Float(string="Handling Amount Limit")
