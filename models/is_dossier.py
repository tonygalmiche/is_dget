# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

#TODO : Je n'ai pas trouvé ces informations dans l'application
# 	# 	Colonne 	Type 	Interclassement 	Attributs 	Null 	Défaut 	Extra 	Action
#	15 	nblogts 	bigint(20) 			Non 	Aucune 		Modifier Modifier 	Supprimer Supprimer 	plus Montrer d'autres actions
#	21 	fiche 	tinyint(1) 			Oui 	NULL 		Modifier Modifier 	Supprimer Supprimer 	plus Montrer d'autres actions

class IsDossier(models.Model):
    _name = 'is.dossier'
    _description = "Dossier"
    _order = 'numaff desc'
    _rec_name = 'numaff'

    numaff               = fields.Char("Numero de dossier", required=True, index=True)
    nom                  = fields.Char("Nom")
    description_succinte = fields.Text("Description succinte")
    adresse1             = fields.Char("Adresse 1")
    adresse2             = fields.Char("Adresse 2")
    codepostal           = fields.Char("Code postal")
    lieu                 = fields.Char("Ville")
    numconcours          = fields.Char("Numéro de concours")
    m_ouvrage_id         = fields.Many2one('res.partner', u"Maitre d'ouvrage")
    m_oeuvre_id          = fields.Many2one('res.partner', u"Maitre d'oeuvre")
    date                 = fields.Date("Date")
    surface              = fields.Float("Surface")
    montant_ope          = fields.Float("Montant de l'opération")
    site_internet        = fields.Char("Site internet")
    description_complete = fields.Text("Description complète")
    nota                 = fields.Text("Note")
    dossierreference     = fields.Selection([('oui','Oui'),('non','Non')],"Dossier référénce")
    fiche                = fields.Selection([('oui','Oui'),('non','Non')],"Fiche")
    distance             = fields.Float("Distance")
    duree                = fields.Float("Durée")
    note_ids             = fields.One2many('is.dossier.note', 'dossier_id', u'Notes')
    referencee_ids       = fields.Many2many('is.dossier.reference', 'is_dossier_is_reference_rel', 'dossier_id', 'reference_id', u'Références')
    contrat_ids          = fields.One2many('is.dossier.contrat', 'dossier_id', u'Contrats')


    @api.multi
    def creation_contrat_action(self, vals):
        for obj in self:
            res= {
                'name': 'Contrat',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.dossier.contrat',
                'type': 'ir.actions.act_window',
                'context': {'default_dossier_id': obj.id }
            }
            return res


class IsDossierNote(models.Model):
    _name = 'is.dossier.note'
    _description = "Dossier Note"
    _order = 'date'
    _rec_name = 'date'

    dossier_id = fields.Many2one('is.dossier', 'Dossier', required=True)
    date       = fields.Date("Date")
    auteur     = fields.Char("Auteur")
    titre      = fields.Char("Titre")
    texte_note = fields.Text("Note")


class IsDossierReference(models.Model):
    _name = 'is.dossier.reference'
    _description = u"Référence Dossier"
    _order = 'name'

    name        = fields.Char(u"Référence dossier", required=True, index=True)
    idreference = fields.Integer(u"idreference")


class IsDossierContratTraitance(models.Model):
    _name = 'is.dossier.contrat.traitance'
    _description = u"Traitance Contrat"
    _order = 'name'

    name = fields.Char(u"Traitance", required=True, index=True)
    code = fields.Char(u"Code")


class IsDossierContrat(models.Model):
    _name = 'is.dossier.contrat'
    _description = u"Contrat"
    _order = 'name'

    name          = fields.Char(u"Numero de contrat", required=True, index=True)
    signe         = fields.Selection([('oui','Oui'),('non','Non')],"Signé")
    dossier_id    = fields.Many2one('is.dossier', u"Dossier", index=True)
    client_id     = fields.Many2one('res.partner', u"Client", index=True)
    description   = fields.Char(u"Description du contrat")
    notes         = fields.Text(u"Notes")
    condreglement = fields.Text(u"Condition de règlement")
    delaipaiement = fields.Text(u"Délai de paiement")
    date          = fields.Date(u"Date")
    refclient     = fields.Char(u"Réf client")
    traitance_id  = fields.Many2one('is.dossier.contrat.traitance', u"Traitance", index=True)


    @api.multi
    def acceder_contrat_action(self, vals):
        for obj in self:
            res= {
                'name': 'Contrat',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.dossier.contrat',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }
            return res













