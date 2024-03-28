# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    target_2022 = fields.Float()
    actual_2022 = fields.Float(compute="_compute_actual_amount")
    target_2023 = fields.Float()
    actual_2023 = fields.Float(compute="_compute_actual_amount")

    def _compute_actual_amount(self):
        for account in self:
            # 2022
            date_from = fields.Date.today().replace(day=1, month=1, year=2022)
            date_to = fields.Date.today().replace(day=31, month=12, year=2022)
            aml_obj = self.env['account.move.line']
            domain = [('account_id', '=', account.id),
                      ('date', '>=', date_from),
                      ('date', '<=', date_to),
                      ('move_id.state', '=', 'posted')
                      ]
            where_query = aml_obj._where_calc(domain)
            aml_obj._apply_ir_rules(where_query, 'read')
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            select = "SELECT sum(credit)-sum(debit) from " + from_clause + " where " + where_clause

            self.env.cr.execute(select, where_clause_params)
            account.actual_2022 = self.env.cr.fetchone()[0] or 0.0
            # 2023
            date_from = fields.Date.today().replace(day=1, month=1, year=2023)
            date_to = fields.Date.today().replace(day=31, month=12, year=2023)
            aml_obj = self.env['account.move.line']
            domain = [('account_id', '=', account.id),
                      ('date', '>=', date_from),
                      ('date', '<=', date_to),
                      ('move_id.state', '=', 'posted')
                      ]
            where_query = aml_obj._where_calc(domain)
            aml_obj._apply_ir_rules(where_query, 'read')
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            select = "SELECT sum(credit)-sum(debit) from " + from_clause + " where " + where_clause

            self.env.cr.execute(select, where_clause_params)
            account.actual_2023 = self.env.cr.fetchone()[0] or 0.0


class AccountMove(models.Model):
    _inherit = "account.move"

    vednor_2_ref = fields.Char(string="Vendor 2. Reference")

    @api.onchange('partner_id', 'currency_id')
    def onchange_partner_bank_id(self):
        company = self.env.user.company_id
        if self.partner_id and self.partner_id.preferred_bank_id:
            self.partner_bank_id = self.partner_id.preferred_bank_id.id
        else:
            if self.currency_id:
                bank = self.env['res.partner.bank'].search([('partner_id', '=', company.partner_id.id), ('currency_id', '=', self.currency_id.id)], limit=1)
                self.partner_bank_id = bank.id


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    notes = fields.Text()
    climaqua_target = fields.Float('Climaqua Target')
    lechuza_target = fields.Float('Lechuza Target')
    coop_target = fields.Float('Coop Target')


class AccountJournal(models.Model):
    _inherit = "account.journal"

    sd_account_number_camt = fields.Char(string="(sd) Account Number Camt")


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    def _check_journal_bank_account(self, journal, account_number):
        '''Override the method to patch for used the IBAN Account and
        Non-IBAN Account to be import from bank statement.
        '''
        if journal.sd_account_number_camt:
            journal_sd_acc_no = journal.sd_account_number_camt.replace('-', '')
            return journal_sd_acc_no == account_number
        else:
            return journal.bank_account_id.sanitized_acc_number == account_number


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'
    _description = "Account Fiscal Position"

    is_deafult_b2b = fields.Boolean(string="Is Default B2b")
