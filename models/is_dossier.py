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
    def name_get(self):
        result = []
        for obj in self:
            result.append((obj.id, str(obj.numaff)+u' - '+str(obj.nom)))
        return result


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        ids = []
        if name:
            ids = self._search(['|',('numaff', 'ilike', name),('nom', 'ilike', name)] + args, limit=limit, access_rights_uid=name_get_uid)
        else:
            ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(ids).name_get()





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
    _order = 'name desc'

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
    invoice_ids   = fields.One2many('account.invoice', 'is_contrat_id', u'Factures')
    detail_ids    = fields.One2many('is.dossier.contrat.detail', 'contrat_id', u'Détail')

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


class IsDossierContratDetail(models.Model):
    _name = 'is.dossier.contrat.detail'
    _description = u"Détail Contrat"
    _order = 'contrat_id,numligne'
    _rec_name = 'numligne'


    @api.depends('montant1','montant2','montant3','montant4')
    def _compute_montant_ht(self):
        for obj in self:
            obj.montant_ht = obj.montant1 + obj.montant2 + obj.montant3 + obj.montant4


    contrat_id  = fields.Many2one('is.dossier.contrat', 'Contrat', required=True, ondelete='cascade')
    numligne    = fields.Integer(u"Ligne", required=True)
    phase_id    = fields.Many2one('is.dossier.contrat.phase', 'Phase')
    texte       = fields.Char(u"Description")
    dateremise  = fields.Date(u"Date")

    stxt1       = fields.Char(u"Description 1")
    montant1    = fields.Float(u"Montant 1", digits=(14,4))
    codass1_id  = fields.Many2one('is.dossier.code.assurance', 'Code assurance 1')

    stxt2       = fields.Char(u"Description 2")
    montant2    = fields.Float(u"Montant 2", digits=(14,4))
    codass2_id  = fields.Many2one('is.dossier.code.assurance', 'Code assurance 2')

    stxt3       = fields.Char(u"Description 3")
    montant3    = fields.Float(u"Montant 3", digits=(14,4))
    codass3_id  = fields.Many2one('is.dossier.code.assurance', 'Code assurance 3')

    stxt4       = fields.Char(u"Description 4")
    montant4    = fields.Float(u"Montant 4", digits=(14,4))
    codass4_id  = fields.Many2one('is.dossier.code.assurance', 'Code assurance 4')

    montant_ht  = fields.Float(u"Montant HT", digits=(14,2), compute='_compute_montant_ht', readonly=True, store=True)

    avancement  = fields.Float(u"Avancement")
    nota        = fields.Char(u"Nota")
    facturable  = fields.Selection([('oui','Oui'),('non','Non')],"Facturable")
    a_facturer  = fields.Float(u"A facturé")
    facture     = fields.Float(u"% facturé")
    facture_le  = fields.Date(u"Pour le")


class IsDossierContratPhase(models.Model):
    _name = 'is.dossier.contrat.phase'
    _description = u"Phase Contrat"
    _order = 'txt_phase'
    _rec_name = 'txt_phase'

    ref_phase       = fields.Integer(u"Ref"     , required=True, index=True)
    txt_phase       = fields.Char(u"Code"       , required=True, index=True)
    det_phase       = fields.Char(u"Description", required=True, index=True)


class IsDossierCodeAssurance(models.Model):
    _name = 'is.dossier.code.assurance'
    _description = u"Code Assurance"
    _order = 'code'
    _rec_name = 'code'

    code        = fields.Char(u"Code"       , required=True, index=True)
    description = fields.Char(u"Description", required=True, index=True)






