
from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_b2b_portal = fields.Boolean(string="B2B Portal")

    def action_b2b_customer_grant_portal_access(self):
        portal_wizard = self.env['portal.wizard'].with_context(active_ids=[self.id]).create({})
        if portal_wizard.user_ids[0].is_portal != True or portal_wizard.user_ids[0].is_internal != True:
            portal_wizard.user_ids[0].action_grant_access()
        elif portal_wizard.user_ids[0].is_portal == True or portal_wizard.user_ids[0].is_internal ==  False:
            portal_wizard.user_ids[0].action_invite_again()

    def write(self, vals):
        if 'website_id' in vals:
            website_id = self.env['website'].browse(vals.get('website_id'))
            if website_id and website_id.is_b2b_website:
                fiscal_id = self.env['account.fiscal.position'].search([('is_deafult_b2b', '=', True)], limit=1)
                vals['property_account_position_id'] = fiscal_id.id
        return super(ResPartner, self).write(vals)
