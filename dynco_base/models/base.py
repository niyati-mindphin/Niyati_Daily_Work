# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @tools.ormcache('self.env.uid', 'self.env.su')
    def _get_tracked_fields(self):
        """ Return the set of tracked fields names for the current model. """
        fields = {
            name
            for name, field in self._fields.items()
            if getattr(field, 'tracking', None) or getattr(field, 'track_visibility', None) or name == 'active'
        }

        return fields and set(self.fields_get(fields))


class Lead(models.Model):
    _inherit = 'crm.lead'

    attachment = fields.Binary(string='attachment', attachment=True)
    brand = fields.Many2one('dr.product.brand', string="Brand")
    year = fields.Char(string="Year")
    company_currency_id = fields.Many2one(
        string='Company Currency',
        related='company_id.currency_id', readonly=True,
    )
    target_amount = fields.Monetary(string="Target Amount", currency_field='company_currency_id')
    is_forecasting = fields.Boolean()

    def action_view_forecast(self):
        action = self.env['ir.actions.act_window']._for_xml_id('dynco_base.action_product_brand_lead')
        action['domain'] = [('opportunity_id', '=', self.id)]
        return action

    @api.onchange('target_amount', 'probability')
    def _onchange_total_amount(self):
        if self.target_amount and self.probability:
            self.expected_revenue = self.target_amount * self.probability / 100

    @api.depends('partner_id.email')
    def _compute_email_from(self):
        return True

    def _inverse_email_from(self):
        return True

class Company(models.Model):
    _inherit = 'res.company'

    ogln = fields.Char(string='O/GLN')
    comp_product_brand_lead_ids = fields.One2many('product.brand.lead', 'res_company_id', string='Brand/Delivery Lead Time')
    background_image = fields.Binary(
        string='Apps Menu Background Image',
        attachment=True
    )
    dynamic_text_1 = fields.Html(
        'dynamic Text one', translate=True)
    dynamic_text_2 = fields.Html(
        'dynamic Text two', translate=True)

    def write(self, vals):
        if vals and vals.get('comp_product_brand_lead_ids'):
            for product_brand_lead in vals.get('comp_product_brand_lead_ids'):
                if isinstance(product_brand_lead[2], dict):
                    if product_brand_lead[2]['delivery_lead_time'] < 1:
                        raise ValidationError(_('You can not Set Delivery LeadTime less than 0.'))
        return super(Company, self).write(vals)


class PartnerShippingMethod(models.Model):
    _name = 'partner.shipping.method'

    partner_id = fields.Many2one('res.partner', string='Customer')
    brand_id = fields.Many2one('dr.product.brand', string="Brand")
    delivery_id = fields.Many2one('delivery.carrier', string="Delivery Method")
    available_carrier_ids = fields.Many2many("delivery.carrier", compute='_compute_available_carrier', string="Available Carriers")

    @api.depends('partner_id')
    def _compute_available_carrier(self):
        for rec in self:
            carriers = self.env['delivery.carrier'].search(['|', ('company_id', '=', False), ('company_id', '=', rec.partner_id.company_id.id or self.env.company.id)])
            rec.available_carrier_ids = carriers.available_carriers(rec.partner_id) if rec.partner_id else carriers
            # breakpoint()

class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _get_default_fc_start_date(self):
        return fields.Date.today().replace(day=1, month=1)

    @api.model
    def _get_default_fc_end_date(self):
        return fields.Date.today().replace(day=31, month=12)

    division_name = fields.Char(string='Division Name')
    gln = fields.Char(string='GLN')
    type = fields.Selection(selection_add=[('field', 'Field Address')])
    business_type = fields.Selection([
        ('b2b', 'Ordinary'),
        ('b2c', 'Webshop')
    ], string='Webshop Price Type', default='b2c')
    eori_no = fields.Char('EORI-No')
    supplier_no = fields.Char()
    product_brand_lead_ids = fields.One2many('product.brand.lead', 'partner_id', string='Brand/Delivery Lead Time')
    preferred_bank_id = fields.Many2one('res.partner.bank', name="Preferred Bank", domain=lambda self: [('partner_id', '=', self.env.user.company_id.partner_id.id)])
    fc_start_date = fields.Date("Start Date", default=_get_default_fc_start_date)
    fc_end_date = fields.Date("End Date", default=_get_default_fc_end_date)
    survey_id = fields.Many2one('survey.survey', name="Survey")
    survey_answer_count = fields.Integer("Survey Answers", compute="_compute_survey_statistic")
    b2b_delivery_method_id = fields.One2many('partner.shipping.method', 'partner_id', name="B2B Delivery Method")
    is_assemble_partner = fields.Boolean('Is Assemble Partner')
    is_portal_user = fields.Boolean('Is Portal', compute="_compute_is_portal_user")

    def _compute_survey_statistic(self):
        for rec in self:
            rec.survey_answer_count = self.env['survey.user_input'].search_count([('partner_survey_id', '=', rec.id)])

    def action_survey_user_input_completed(self):
        action = self.env['ir.actions.act_window']._for_xml_id('survey.action_survey_user_input')
        ctx = dict(self.env.context)
        ctx.update({
            'search_default_completed': 1,
            'search_default_not_test': 1
        })
        action['context'] = ctx
        action['domain'] = [('partner_survey_id', '=', self.id)]
        return action

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['ref'] = self.env['ir.sequence'].next_by_code('partner.seq')
        return super(Partner, self).create(vals_list)

    def write(self, vals):
        if vals and vals.get('product_brand_lead_ids'):
            for product_brand_lead in vals.get('product_brand_lead_ids'):
                if isinstance(product_brand_lead[2], dict):
                    if 'delivery_lead_time' in product_brand_lead[2] and product_brand_lead[2]['delivery_lead_time'] < 1:
                        raise ValidationError(_('You can not Set Delivery LeadTime less than 0.'))
        return super(Partner, self).write(vals)
    # commercial_number = fields.Char(
    #     string='Commercial Partner ID',
    #     compute='_compute_commercial_number', recursive=True, store=False)

    # already exist 'commercial_partner_id' but used ref field from partner in v15

    # @api.depends('is_company', 'parent_id.commercial_number')
    # def _compute_commercial_number(self):
    #     for partner in self:
    #         if (partner.is_company or
    #                 not partner.parent_id or
    #                 partner.type == 'other'):
    #             # partner.commercial_number = partner.partner_number
    #             partner.commercial_number = partner.ref
    #         else:
    #             partner.commercial_number = (
    #                 partner.parent_id.commercial_number)

    def _compute_is_portal_user(self):
        user = self.env['res.users'].search([('partner_id', '=', self.id)])
        portal_user = user.has_group('base.group_portal')
        if portal_user:
            self.is_portal_user = True
        else:
            self.is_portal_user = False

    def btn_impersonate_user(self):
        user = self.env['res.users'].search([('partner_id', '=', self.id)])
        if user:
           return user.btn_impersonate_user()
        else:
            raise UserError(_("User not created for this Customer!"))


    def action_open_survey(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': "Open Survey",
            'target': '_blank',
            'url': '/survey/start/%s/%d' % (self.survey_id.access_token, self.id)
        }

    def name_get(self):
        res = []
        for partner in self:
            name = partner.name or ''
            if partner.division_name:
                division_name = partner.division_name
                name += "\n" + division_name

            if partner.company_name or partner.parent_id:
                if not name and partner.type in ['invoice', 'delivery', 'other']:
                    name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                if not partner.is_company:
                    name = "%s, %s" % (partner.commercial_company_name or partner.parent_id.name, name)
            if self._context.get('show_address_only'):
                name = partner._display_address(without_company=True)
            if self._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if self._context.get('show_email') and partner.email:
                name = "%s <%s>" % (name, partner.email)
            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')
            res.append((partner.id, name))
        return res

    def _get_name(self):
        """ Utility method to allow name_get to be overrided without re-browse the partner """
        partner = self
        name = partner.name or ''

        if partner.division_name:
                division_name = partner.division_name
                name += "\n" + division_name
        if partner.company_name or partner.parent_id:
            if not name and partner.type in ['invoice', 'delivery', 'other']:
                name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
            if not partner.is_company:
                name = self._get_contact_name(partner, name)
        if self._context.get('show_address_only'):
            name = partner._display_address(without_company=True)
        if self._context.get('show_address'):
            name = name + "\n" + partner._display_address(without_company=True)
        name = name.replace('\n\n', '\n')
        name = name.replace('\n\n', '\n')
        if self._context.get('partner_show_db_id'):
            name = "%s (%s)" % (name, partner.id)
        if self._context.get('address_inline'):
            splitted_names = name.split("\n")
            name = ", ".join([n for n in splitted_names if n.strip()])
        if self._context.get('show_email') and partner.email:
            name = "%s <%s>" % (name, partner.email)
        if self._context.get('html_format'):
            name = name.replace('\n', '<br/>')
        if self._context.get('show_vat') and partner.vat:
            name = "%s ‒ %s" % (name, partner.vat)
        return name

    def compute_delivered_untaxed_amnt_total(self, line_pro_brand, partners):
        ''' Compute : Delivered Untaxed Amount Total'''
        delivered_price_subtotal = 0.0
        SOL = self.env['sale.order.line']
        sale_order_line_groups = SOL.read_group(
            domain=[('order_id.partner_id', 'in', partners.ids),
                    ('product_id.product_brand_lead', '=', line_pro_brand.product_brand_lead.id),
                    ('order_id.date_order', '>=', self.fc_start_date),
                    ('order_id.date_order', '<=', self.fc_end_date),
                    ('order_id.state', 'in', ('done', 'complete', 'sale'))],
            fields=['delivered_price_subtotal'], groupby=['order_id'])
        if sale_order_line_groups:
            for line_untaxed_amnt in sale_order_line_groups:
                delivered_price_subtotal += line_untaxed_amnt['delivered_price_subtotal']
        return delivered_price_subtotal

    def compute_invoiced_untaxed_amnt_total(self, line_pro_brand, partners):
        ''' Compute : Delivered Untaxed Amount Total'''
        invoiced_price_subtotal = 0.0
        AML = self.env['account.move.line']
        account_move_line_groups = AML.read_group(
            domain=[('move_id.partner_id', 'in', partners.ids),
                    ('move_id.move_type', '=', 'out_invoice'),
                    ('product_id.product_brand_lead', '=', line_pro_brand.product_brand_lead.id),
                    ('move_id.invoice_date', '>=', self.fc_start_date),
                    ('move_id.invoice_date', '<=', self.fc_end_date),
                    ('move_id.state', 'in', ['draft', 'posted'])],
            fields=['price_subtotal'], groupby=['move_id'])
        if account_move_line_groups:
            for line_untaxed_amnt in account_move_line_groups:
                invoiced_price_subtotal += line_untaxed_amnt['price_subtotal']
        return invoiced_price_subtotal

    def compute_untaxed_amnt_total(self, line_pro_brand, partners):
        ''' Compute : Untaxed Amount Total'''
        price_subtotal = 0.0
        SOL = self.env['sale.order.line']
        sale_order_line_groups = SOL.read_group(
            domain=[('order_id.partner_id', 'in', partners.ids),
                    ('product_id.product_brand_lead', '=', line_pro_brand.product_brand_lead.id),
                    ('order_id.date_order', '>=', self.fc_start_date),
                    ('order_id.date_order', '<=', self.fc_end_date),
                    ('order_id.invoice_status', '=', 'invoiced')],
            fields=['price_subtotal'], groupby=['order_id'])
        if sale_order_line_groups:
            for line_untaxed_amnt in sale_order_line_groups:
                price_subtotal += line_untaxed_amnt['price_subtotal']
        return price_subtotal

    def compute_credit_note_total(self, line_pro_brand, partners):
        ''' Compute : Credit Note Total'''
        credit_note_total = 0.0
        InvoiceLine = self.env['account.move.line']
        invoice_line_group = InvoiceLine.read_group(
            domain=[('move_id.partner_id', 'in', partners.ids),
                    ('move_id.move_type', '=', 'out_refund'),
                    ('product_id.product_brand_lead', '=', line_pro_brand.product_brand_lead.id),
                    ('move_id.invoice_date', '>=', self.fc_start_date),
                    ('move_id.invoice_date', '<=', self.fc_end_date),
                    ('move_id.state', 'not in', ['draft', 'cancel'])],
            fields=['price_subtotal'], groupby=['move_id'])
        if invoice_line_group:
            for line_untaxed_amnt in invoice_line_group:
                credit_note_total += line_untaxed_amnt['price_subtotal']
        return credit_note_total

    def compute_margin(self, line_pro_brand, partners):
        ''' Compute : Untaxed Amount Total'''
        margin = compute_margin_per = 0.0
        SOL = self.env['sale.order.line']
        sale_order_line_groups = SOL.read_group(
            domain=[('order_id.partner_id', 'in', partners.ids),
                    ('product_id.product_brand_lead', '=', line_pro_brand.product_brand_lead.id),
                    ('order_id.date_order', '>=', self.fc_start_date),
                    ('order_id.date_order', '<=', self.fc_end_date),
                    ('order_id.invoice_status', '=', 'invoiced')],
            fields=['margin', 'price_unit', 'knk_purchase_price'], groupby=['order_id'])
        if sale_order_line_groups:
            for line_untaxed_amnt in sale_order_line_groups:
                margin += line_untaxed_amnt['margin']
                compute_margin_per = (line_untaxed_amnt['price_unit'] - line_untaxed_amnt['knk_purchase_price']) / (line_untaxed_amnt['price_unit'] * 100) if line_untaxed_amnt['price_unit'] > 0 else 1
        return margin, compute_margin_per

    def action_customer_forecast(self):
        ''' Customer Forecast'''
        partners = self.search([('id', 'child_of', self.ids)])
        partners.read(['parent_id'])
        ProductBrandLead = self.env['product.brand.lead']
        total_brand = self.env['dr.product.brand'].search([('name', '=', _('TOTAL'))], limit=1)
        lines = self.env['product.brand.lead'].search([('partner_id', '=', self.id), ('fc_year', '=', self.fc_start_date.year)])
        if not lines:
            for index, line in enumerate(self.company_id.comp_product_brand_lead_ids):
                lines |= ProductBrandLead.create({'partner_id': self.id, 'sequence': int(self.fc_start_date.year) + index, 'fc_year': self.fc_start_date.year, 'product_brand_lead': line.product_brand_lead.id, 'delivery_lead_time': line.delivery_lead_time})
            lines |= ProductBrandLead.create({'partner_id': self.id, 'sequence': int(self.fc_start_date.year) + 100, 'fc_year': self.fc_start_date.year, 'product_brand_lead': total_brand.id, 'is_total': True})
        total_delivered_untaxed_amt = total_invoiced_untaxed_amt = 0.0
        total_credit_note_total = 0.0
        total_total_amount = 0.0
        total_target_value = 0.0
        if not self.env['product.brand.lead'].search([('product_brand_lead', '=', total_brand.id), ('partner_id', '=', self.id), ('fc_year', '=', self.fc_start_date.year)], limit=1):
            lines |= ProductBrandLead.create({'partner_id': self.id, 'fc_year': self.fc_start_date.year, 'product_brand_lead': total_brand.id, 'is_total': True})
        for line_pro_brand in lines.sorted(lambda x: x.sequence):
            if not line_pro_brand.is_total:
                untaxed_amnt_total = self.compute_untaxed_amnt_total(line_pro_brand, partners)
                delivered_untaxed_amnt_total = self.compute_delivered_untaxed_amnt_total(line_pro_brand, partners)
                invoiced_untaxed_amnt_total = self.compute_invoiced_untaxed_amnt_total(line_pro_brand, partners)
                credit_note_total = self.compute_credit_note_total(line_pro_brand, partners)
                compute_margin, compute_margin_per = self.compute_margin(line_pro_brand, partners)
                line_pro_brand.write({
                    'untaxed_amnt_total': untaxed_amnt_total,
                    'delivered_untaxed_amt': delivered_untaxed_amnt_total,
                    'invoiced_untaxed_amt': invoiced_untaxed_amnt_total,
                    'credit_note_total': credit_note_total,
                    'compute_margin': compute_margin,
                    'compute_margin_per': compute_margin_per,
                    'total_amount': invoiced_untaxed_amnt_total - credit_note_total,
                    # 'percentage_value': ((delivered_untaxed_amnt_total - credit_note_total) * 100) / line_pro_brand.target_value if line_pro_brand.target_value > 0 else 1,
                    'target_margin_percentage': line_pro_brand.target_margin / compute_margin if compute_margin != 0 else 1,
                })
                total_delivered_untaxed_amt += delivered_untaxed_amnt_total
                total_invoiced_untaxed_amt += invoiced_untaxed_amnt_total
                total_credit_note_total += credit_note_total
                total_total_amount += (invoiced_untaxed_amnt_total - credit_note_total)
                total_target_value += line_pro_brand.target_value
            if line_pro_brand.is_total:
                line_pro_brand.write({
                    'delivered_untaxed_amt': total_delivered_untaxed_amt,
                    'invoiced_untaxed_amt': total_invoiced_untaxed_amt,
                    'credit_note_total': total_credit_note_total,
                    'total_amount': total_total_amount,
                    'target_value': total_target_value,
                })

    @api.model
    def set_target_values_move_line(self):
        for partner in self.search([]):
            for record in partner.product_brand_lead_ids:
                if record.partner_id and record.fc_year and record.product_brand_lead.name in [_('Lechuza'),_('CLIMAQUA'),_('Coop Premium Home')]:
                    start_date = fields.Date.today().replace(day=1, month=1, year=int(record.fc_year))
                    end_date = fields.Date.today().replace(day=31, month=12, year=int(record.fc_year))
                    line = self.env['account.move.line'].search([
                        ('move_id.partner_id', '=', record.partner_id.id),
                        ('move_id.move_type', '=', 'out_invoice'),
                        ('move_id.invoice_date', '>=', start_date),
                        ('move_id.invoice_date', '<=', end_date),
                        ('exclude_from_invoice_tab', '=', False),
                        ('product_id.product_brand_lead', '=', record.product_brand_lead.id),
                    ], limit=1)
                    if line:
                        if record.product_brand_lead.name == _('CLIMAQUA'):
                            line.write({'climaqua_target': record.target_value})
                        elif record.product_brand_lead.name == _('Lechuza'):
                            line.write({'lechuza_target': record.target_value})
                        elif record.product_brand_lead.name == _('Coop Premium Home'):
                            line.write({'coop_target': record.target_value})


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    delivey_time = fields.Char(related="website_id.delivey_time", readonly=False)


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    invoice_issuer_number = fields.Char('Invoice Issuer Number')


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    @api.model
    def _default_bank_journal_id(self):
        default_company_id = self.default_get(['company_id'])['company_id']
        return self.env['account.journal'].search([('type', '=', 'cash'), ('company_id', '=', default_company_id)], limit=1)

    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', states={'done': [('readonly', True)], 'post': [('readonly', True)]}, check_company=True, domain="[('type', 'in', ['cash', 'bank']), ('company_id', '=', company_id)]",
        default=_default_bank_journal_id, help="The payment method used when the expense is paid by the company.")


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    partner_survey_id = fields.Many2one('res.partner', string='Customer')
