# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class IsTVA(models.Model):
    _name = 'is.tva'
    _description = u"Fiche pour gérer la TVA et le compte de vente sur les factures"
    _order = 'name'

    name       = fields.Char(u"TVA", required=True, index=True)
    tax_id     = fields.Many2one('account.tax'    , u'Taxe à la vente', required=True)
    account_id = fields.Many2one('account.account', u'Compte de vente', required=True)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.depends('is_contrat_id')
    def _compute_dossier_id(self):
        for obj in self:
            obj.is_dossier_id = obj.is_contrat_id.dossier_id.id

    @api.depends('is_contrat_id')
    def _compute_total_contrat_ht(self):
        for obj in self:
            is_total_contrat_ht = 0
            for line in obj.is_contrat_id.detail_ids:
                is_total_contrat_ht += line.montant_ht
            obj.is_total_contrat_ht = is_total_contrat_ht

    @api.depends('invoice_line_ids')
    def _compute_montant_revision(self):
        for obj in self:
            montant = 0
            for line in obj.invoice_line_ids:
                if line.product_id.name==u'Révisions':
                    montant += line.price_unit*line.quantity
            obj.is_montant_revision = montant

    is_contrat_id       = fields.Many2one('is.dossier.contrat', u'Contrat', index=True)
    is_total_contrat_ht = fields.Float(u"Total contrat HT", digits=(14,2), compute='_compute_total_contrat_ht', readonly=True, store=False)
    is_montant_revision = fields.Float(u"Montant révision", digits=(14,4), compute='_compute_montant_revision', readonly=True, store=True)
    is_dossier_id       = fields.Many2one('is.dossier', u"Dossier"       , compute='_compute_dossier_id'      , readonly=True, store=True, index=True)
    is_tva_id           = fields.Many2one('is.tva', u'TVA')

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


    @api.multi
    def update_tva_account_action(self):
        for obj in self:
            for line in obj.invoice_line_ids:
                line.account_id = obj.is_tva_id.account_id.id
                line.invoice_line_tax_ids = [(6,0,[obj.is_tva_id.tax_id.id])]
            obj.compute_taxes()
        return True

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    _order = 'is_contrat_detail_id'

    is_contrat_detail_id = fields.Many2one('is.dossier.contrat.detail', u'Ligne Contrat', index=True)

    @api.multi
    def uptate_onchange_product_id(self):
        for obj in self:
            obj._onchange_product_id()
            #obj._compute_price()
            #obj._set_taxes()
            obj.invoice_id.compute_taxes()

        return True

