# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class IsClassement(models.Model):
    _name = 'is.classement'
    _description = "Classement"
    _order = 'name'

    name = fields.Char("Classement", required=True, index=True)


class IsSpecialite(models.Model):
    _name = 'is.specialite'
    _description = "Spécialité"
    _order = 'name'

    name = fields.Char("Spécialité", required=True, index=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_prefixe         = fields.Char(u"Préfixe")
    is_numero          = fields.Integer(u"Numéro")
    is_service         = fields.Char(u"Service")
    is_specialite      = fields.Char(u"Spécialité(s)")
    is_specialite_ids  = fields.Many2many('is.specialite', 'res_partner_is_specialite_rel', 'partner_id', 'specialite_id', u'Spécialités')
    is_classement_id   = fields.Many2one('is.classement', "Classement")


    # Permet de désactiver le controle de la TVA
    @api.constrains('vat')
    def check_vat(self):
        return True

