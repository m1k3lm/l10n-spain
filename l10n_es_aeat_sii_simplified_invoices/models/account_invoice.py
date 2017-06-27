# -*- coding: utf-8 -*-
# Copyright 2017 Santa Fixie SL - Juanjo Algaz <jalgaz@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import _, api, exceptions, fields, models
from openerp.tools.float_utils import float_round

_logger = logging.getLogger(__name__)

try:
    from openerp.addons.connector.queue.job import job
    from openerp.addons.connector.session import ConnectorSession
except ImportError:
    _logger.debug('Can not `import connector`.')
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial
    job = empty_decorator_factory


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'


    @api.multi
    def _sii_check_exceptions(self):
        """Inheritable method for exceptions control when sending SII invoices.
        """
        self.ensure_one()
        if (not self.fiscal_position and not self.partner_id.vat) or \
            (self.fiscal_position and self.fiscal_position.vat_required and not
                self.partner_id.vat):
            raise exceptions.Warning(
                _("The partner has not a VAT configured.")
            )
        if not self.company_id.chart_template_id:
            raise exceptions.Warning(_(
                'You have to select what account chart template use this'
                ' company.'))
        if not self.company_id.sii_enabled:
            raise exceptions.Warning(
                _("This company doesn't have SII enabled.")
            )

    @api.multi
    def _get_sii_invoice_dict_out(self, cancel=False):
        """Build dict with data to send to AEAT WS for invoice types:
        out_invoice and out_refund.

        :param cancel: It indicates if the dictionary if for sending a
          cancellation of the invoice.
        :return: invoices (dict) : Dict XML with data for this invoice.
        """
        self.ensure_one()
        invoice_date = self._change_date_format(self.date_invoice)
        company = self.company_id
        ejercicio = fields.Date.from_string(
            self.period_id.fiscalyear_id.date_start).year
        periodo = '%02d' % fields.Date.from_string(
            self.period_id.date_start).month

        inv_dict = {
            "IDFactura": {
                "IDEmisorFactura": {
                    "NIF": company.vat[2:],
                },
                "NumSerieFacturaEmisor": self.number[0:60],
                "FechaExpedicionFacturaEmisor": invoice_date,
            },
            "PeriodoImpositivo": {
                "Ejercicio": ejercicio,
                "Periodo": periodo,
            },
        }
        if not cancel:
            if (self.fiscal_position and self.fiscal_position.vat_required) or \
                    (not self.fiscal_position):
                vat_required = True
                tipo_factura = 'F1'
            else:
                vat_required = False

            if not vat_required and self.type == 'out_invoice':
                # factura simplificada
                tipo_factura = 'F2'
            elif vat_required and self.type == 'out_refund':
                tipo_factura = 'R4'
            elif not vat_required and self.type == 'out_refund':
                # factura simplificada
                tipo_factura = 'R5'
            # Check if refund type is 'By differences'. Negative amounts!
            sign = -1.0 if self.sii_refund_type == 'I' else 1.0
            inv_dict["FacturaExpedida"] = {
                # TODO: Incluir los 5 tipos de facturas rectificativas
                "TipoFactura": tipo_factura,
                "ClaveRegimenEspecialOTrascendencia": (
                    self.sii_registration_key.code
                ),
                "DescripcionOperacion": self.sii_description[0:500],
                "Contraparte": {
                    "NombreRazon": self.partner_id.name[0:120],
                },
                "TipoDesglose": self._get_sii_out_taxes(),
                "ImporteTotal": float_round(self.amount_total * sign, 2),
            }
            exp_dict = inv_dict['FacturaExpedida']
            if vat_required:
                # Uso condicional de IDOtro/NIF
                exp_dict['Contraparte'].update(self._get_sii_identifier())
            else:
                # simplificada, no es necesario datos de contraparte
                del exp_dict['Contraparte']
            if self.type == 'out_refund':
                exp_dict['TipoRectificativa'] = self.sii_refund_type
                if self.sii_refund_type == 'S':
                    exp_dict['ImporteRectificacion'] = {
                        'BaseRectificada': sum(
                            self.mapped('origin_invoices_ids.amount_untaxed')
                        ),
                        'CuotaRectificada': sum(
                            self.mapped('origin_invoices_ids.amount_tax')
                        ),
                    }
        return inv_dict
