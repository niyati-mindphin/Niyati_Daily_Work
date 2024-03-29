from odoo import fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    website_id = fields.Many2one('website', ondelete='cascade', string="Website")

    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        res = super(CrmLead, self)._prepare_customer_values(partner_name, is_company, parent_id)
        if self.website_id:
            res['website_id'] = self.website_id.id
        return res

    def action_b2b_customer(self):
        view_id = self.env.ref('b2b_portal.view_res_partner_form_mdpn').id
        context = self._context.copy()
        partner = self.partner_id
        if self.partner_id.parent_id:
            partner = self.partner_id.parent_id
        partner.is_b2b_portal = True
        return {
            'name':'B2B Customer',
            'view_type':'form',
            'view_mode':'tree',
            'views' : [(view_id,'form')],
            'res_model':'res.partner',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'res_id':partner.id,
            'target':'new',
            'context':context,
        }
