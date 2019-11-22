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
    nota                 = fields.Text("Notes")
    dossierreference     = fields.Selection([('oui','Oui'),('non','Non')],"Dossier référénce")
    fiche                = fields.Selection([('oui','Oui'),('non','Non')],"Fiche")
    distance             = fields.Float("Distance")
    duree                = fields.Float("Durée")


