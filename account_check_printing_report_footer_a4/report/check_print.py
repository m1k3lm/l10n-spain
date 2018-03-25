# -*- coding: utf-8 -*-

import time
from . import lang_ES
from odoo import _, api, exceptions, models


class ReportCheckPrint(models.AbstractModel):
    _name = 'report.account_check_printing_report_footer_a4.check_footer_a4'
    _inherit = 'report.account_check_printing_report_base.report_check_base'

    def amount2words(self, amount):
        return lang_ES.num2words_es(
            amount, to='currency', lang=self.env.context.get('lang', 'en_US'))

    @api.multi
    def render_html(self, docids, data=None):
        payments = self.env['account.payment'].browse(docids)
        paid_lines = self.get_paid_lines(payments)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': payments,
            'time': time,
            'fill_stars': self.fill_stars,
            'paid_lines': paid_lines,
            'num2words': self.amount2words,
        }
        if self.env.user.company_id.check_layout_id:
            return self.env['report'].render(
                self.env.user.company_id.check_layout_id.report,
                docargs)
        raise exceptions.Warning(_('You must define a check layout'))
