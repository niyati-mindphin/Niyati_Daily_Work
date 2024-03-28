# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    privacy_visibility = fields.Selection(selection_add=[('private_users', 'Private Project - Visible by selected users only')], ondelete={'private_users': 'set default'})
    private_project_users = fields.Many2many('res.users', 'user_id', 'project_id', 'rel_user_project_id', string='Users', default=lambda self: self.env.user)

    def write(self, vals):
        for rec in self:
            if rec.privacy_visibility == 'private_users' or vals.get('privacy_visibility') == 'private_users':
                if vals.get('user_id') and not vals.get('private_project_users'):
                    if vals.get('user_id') not in rec.private_project_users.ids and self.env.user.id != vals.get('user_id'):
                        raise UserError(_("You should be atleast in Users or as a Project Manager !"))
                if not vals.get('user_id') and vals.get('private_project_users'):
                    if self.env.user.id not in vals.get('private_project_users')[0][2] and self.env.user != rec.user_id:
                        raise UserError(_("You should be atleast in Users or as a Project Manager !"))
                if vals.get('user_id') and vals.get('private_project_users'):
                    if self.env.user.id not in vals.get('private_project_users')[0][2] and self.env.user.id != vals.get('user_id'):
                        raise UserError(_("You should be atleast in Users or as a Project Manager !"))
        return super(ProjectProject, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('privacy_visibility') == 'private_users':
            if self.env.user.id not in vals.get('private_project_users')[0][2] and self.env.user.id != vals.get('user_id'):
                raise UserError(_("You should be atleast in Users or as a Project Manager !"))
        return super(ProjectProject, self).create(vals)
