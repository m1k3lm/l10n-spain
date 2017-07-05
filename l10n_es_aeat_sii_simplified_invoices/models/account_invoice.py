# -*- coding: utf-8 -*-
# Copyright 2017 Santa Fixie SL - Juanjo Algaz <jalgaz@gmail.com>
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import _, api, exceptions, models

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _sii_check_exceptions(self):
        if not self._vat_required():
            if not self.company_id.max_amount_total_simplified_invoice:
                raise exceptions.Warning(
                    _("The company does not have the maximum amount indicated "
                      "for simplified invoices (company form).")
                )
            if (self.amount_total >
                    self.company_id.max_amount_total_simplified_invoice):
                raise exceptions.Warning(
                    _("This invoice can not be simplified type, the amount "
                      "total is above the limit (company form).")
                )
        super(AccountInvoice, self)._sii_check_exceptions()

    @api.multi
    def _get_sii_invoice_dict_out(self, cancel=False):
        if not self.fiscal_position.vat_required:
            self.partner_id.commercial_partner_id.update({
                'sii_simplified_invoice': True,
            })
        inv_dict = super(AccountInvoice, self)._get_sii_invoice_dict_out(
            cancel=cancel,
        )
        if not self.fiscal_position.vat_required:
            self.partner_id.commercial_partner_id.update({
                'sii_simplified_invoice': False,
            })
        return inv_dict
