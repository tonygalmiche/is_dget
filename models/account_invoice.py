# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.depends('is_contrat_id')
    def _compute_dossier_id(self):
        for obj in self:
            obj.is_dossier_id = obj.is_contrat_id.dossier_id.id

    is_contrat_id = fields.Many2one('is.dossier.contrat', u'Contrat', index=True)
    is_dossier_id = fields.Many2one('is.dossier', u"Dossier"        , index=True, compute='_compute_dossier_id', readonly=True, store=True)

    @api.multi
    def acceder_facture_action(self, vals):
        for obj in self:

            res= {
                'name': 'Facture',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'account.invoice',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref('account.invoice_form').id,
                'domain': [('type','=','out_invoice')],
            }
            return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.multi
    def uptate_onchange_product_id(self):
        for obj in self:
            obj._onchange_product_id()
            #obj._compute_price()
            #obj._set_taxes()
            obj.invoice_id.compute_taxes()

        return True

