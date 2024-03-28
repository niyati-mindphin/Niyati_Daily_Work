# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductBrandLead(models.Model):
    _name = "product.brand.lead"
    _description = "Brand and Delivery Lead Time"

    sequence = fields.Integer()
    product_brand_lead = fields.Many2one('dr.product.brand', string='Product Brand', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    res_company_id = fields.Many2one('res.company', string='Company')
    delivery_lead_time = fields.Integer(string="Del.Lead Time")
    untaxed_amnt_total = fields.Monetary(string="Untaxed Amt Total")
    credit_note_total = fields.Monetary(string="Credit Note Total")
    total_amount = fields.Monetary(string="Total Turnover")
    target_value = fields.Monetary(string="Target Value")
    compute_margin = fields.Monetary(string="Margin This Year")
    compute_margin_per = fields.Float(string="Margin % This Year")
    target_margin = fields.Monetary(string="Target Margin")
    target_margin_percentage = fields.Float(string="Target Margin Percentage")
    percentage_value = fields.Float(compute="_compute_percentage_value", store=True, string="Percentage")
    currency_id = fields.Many2one("res.currency", string="Currency", related='partner_id.property_product_pricelist.currency_id', readonly=True)
    delivered_untaxed_amt = fields.Monetary(string="Del.Untaxed Amt Total")
    invoiced_untaxed_amt = fields.Monetary(string="Inv.Untaxed Amt Total")
    fc_year = fields.Char(string="Year")
    is_total = fields.Boolean()
    partner_tags = fields.Many2many(related="partner_id.category_id", string="Partner Tags")
    saleperson_id = fields.Many2one(string="Salesperson", related='partner_id.user_id', store=True)
    partner_zip = fields.Char(string="Zip Code", related='partner_id.zip', store=True)
    opportunity_id = fields.Many2one('crm.lead', string="Opportunity")

    @api.onchange('product_brand_lead')
    def _onchnage_product_brand_lead(self):
        if self.product_brand_lead:
            lead = self.search([('res_company_id', '=', self.env.user.company_id.id), ('product_brand_lead', '=', self.product_brand_lead.id)], limit=1)
            self.delivery_lead_time = lead.delivery_lead_time

    @api.depends('invoiced_untaxed_amt', 'target_value')
    def _compute_percentage_value(self):
        for record in self:
            record.percentage_value = (record.invoiced_untaxed_amt * 100) / record.target_value if record.target_value > 0 else 1

    def write(self, vals):
        res = super(ProductBrandLead, self).write(vals)
        if 'target_value' in vals:
            for record in self:
                if record.partner_id and record.product_brand_lead.name in [_('Lechuza'),_('CLIMAQUA'),_('Coop Premium Home')]:
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
        return 

    def action_forecasted_leads(self):
        for rec in self:
            if rec.product_brand_lead and rec.fc_year:
                vals = {
                    'name': rec.partner_id.name,
                    'partner_id': rec.partner_id.id,
                    'brand': rec.product_brand_lead.id,
                    'year': rec.fc_year,
                    'target_amount': rec.target_value,
                    'type': 'opportunity',
                    'is_forecasting': True,
                }
                if rec.opportunity_id:
                    rec.opportunity_id.write(vals)
                else:
                    opportunity = self.env['crm.lead'].create(vals)
                    rec.opportunity_id = opportunity
        return

    def action_view_opportunity(self):
        action = self.env['ir.actions.act_window']._for_xml_id('crm.crm_lead_action_pipeline')
        action['domain'] = [('id', '=', self.opportunity_id.id)]
        return action
