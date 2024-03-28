# -*- coding: utf-8 -*-
# import sys
import xlwt
import io
import base64
import json
from . import format_common

from odoo import fields, models, _


class AccountInvocexlsList(models.TransientModel):
    _name = "account.move.xls.list"
    _description = "Move Excel Report"

    def _get_xls(self):
        workbook = xlwt.Workbook()
        header_tstyle_c = format_common.font_style(position='center', bold=1, border=1, fontos='black', font_height=180, color='grey')
        # other_tstyle = format_common.font_style(position='left', fontos='black', font_height=180)
        other_tstyle_c = format_common.font_style(position='center', fontos='black', font_height=180)

        sheet = workbook.add_sheet('Invoice')
        sheet.write_merge(0, 0, 0, 6, u'Invoice report', header_tstyle_c)
        sheet.write(2, 0, u'Date:', header_tstyle_c)
        sheet.write(2, 1, fields.date.today(), other_tstyle_c)

        sheet.write(4, 0, 'Supplier#', header_tstyle_c)
        sheet.write(4, 1, 'Supp Name', header_tstyle_c)
        sheet.write(4, 2, 'PO#', header_tstyle_c)
        sheet.write(4, 3, 'PO Date', header_tstyle_c)
        sheet.write(4, 4, 'Days', header_tstyle_c)
        sheet.write(4, 5, 'PO Amount', header_tstyle_c)
        sheet.write(4, 6, 'Supp Inv', header_tstyle_c)

        stream = io.BytesIO()
        workbook.save(stream)

        return base64.encodestring(stream.getvalue())

    name = fields.Char(size=256)
    xls_output = fields.Binary(string='Excel output', readonly="1", default=_get_xls)

    def print_report(self):
        invoice_ids = self.env.context.get('active_ids')
        leninv = 0
        workbook = xlwt.Workbook(encoding='utf-8')
        name = ''
        attach_id = False
        header_tstyle_c = format_common.font_style(position='center', bold=1, border=1, fontos='black', font_height=180, color='grey')
        other_tstyle = format_common.font_style(position='left', fontos='black', font_height=180)
        other_tstyle_c = format_common.font_style(position='center', fontos='black', font_height=180)
        row = 0
        tax_name_list = []
        for invoice in self.env['account.move'].browse(invoice_ids):
            for dt in json.loads(invoice.tax_totals_json)['groups_by_subtotal'].get(_('Untaxed Amount'), []):
                tax_name_list.append(dt['tax_group_name'])
        sheet = workbook.add_sheet("Invoice")
        sheet.write(row, 0, 'Invoice', header_tstyle_c)
        sheet.write(row, 1, 'Customer Name', header_tstyle_c)
        sheet.write(row, 2, 'Account', header_tstyle_c)
        sheet.write(row, 3, 'Net Amount', header_tstyle_c)

        tr = 4
        tax_len = len(tax_name_list)
        for t in tax_name_list:
            sheet.write(row, tr, t, header_tstyle_c)
            tr += 1

        sheet.col(tr).width = 256 * 20
        sheet.write(row, tr, 'VAT-ID', header_tstyle_c)

        sheet.col(0).width = 256 * 20
        sheet.col(1).width = 256 * 50

        row = 1
        for invoice in self.env['account.move'].browse(invoice_ids):
            if invoice.state not in ('draft', 'cancel'):
                leninv += 1
                name = ''
                code = ''
                if invoice.partner_id.parent_id:
                    name = invoice.partner_id.parent_id.name
                elif invoice.partner_id:
                    name = invoice.partner_id.name
                if invoice.partner_id.parent_id.property_account_receivable_id:
                    code = invoice.partner_id.parent_id.property_account_receivable_id.code
                elif invoice.partner_id.property_account_receivable_id:
                    code = invoice.partner_id.property_account_receivable_id.code

                sheet.write(row, 0, invoice.name or '', other_tstyle)
                sheet.write(row, 1, name, other_tstyle)
                sheet.write(row, 2, code, other_tstyle_c)
                sheet.write(row, 3, invoice.amount_untaxed, other_tstyle_c)
                trv = 4
                tax_total = 0
                for dt in json.loads(invoice.tax_totals_json)['groups_by_subtotal'].get(_('Untaxed Amount'), []):
                    tax_total += dt['tax_group_amount']

                sheet.write(row, trv, tax_total, header_tstyle_c)
                trv += 1
                sheet.write(row, tax_len+trv-1, invoice.partner_id.vat or '', other_tstyle_c)

                row += 1
                stream = io.BytesIO()
                workbook.save(stream)
                self._cr.execute(""" DELETE FROM output""")
                name = _("Invoices List")
                attach_id = self.env['output.list'].create({'name': name+'.xls', 'xls_output': base64.encodestring(stream.getvalue())})

        return {
                'name': _('Invoice XLS'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'output.list',
                'view_id': self.env.ref('dynco_base.account_xls_list_output_view').id,
                'type': 'ir.actions.act_window',
                'res_id': attach_id and attach_id.id or False,
                'context': self.env.context,
                'target': 'new'
            }


class Output(models.TransientModel):
    _name = 'output'
    _description = "Bounce file Output"
