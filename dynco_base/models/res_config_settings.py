# -*- coding: utf-8 -*-
from odoo import api, fields, models, modules


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    login_background_image = fields.Binary(string="Login Background Image", related='website_id.login_background_image', readonly=False)
    dropship_delivery_partner_id = fields.Many2one('res.partner',
        config_parameter= 'dynco_base.dropship_delivery_partner_id', string= 'Dropship Delivery Partner')
