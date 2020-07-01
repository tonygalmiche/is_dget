# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import datetime
from odoo.exceptions import Warning


def _get_prefix_annee():
    annee = datetime.date.today().year
    annee = annee-1989
    x = str(datetime.date.today())[-5:]
    if x>='04-01':
        annee+=1 # Si 1er avril, prendre l'année suivante
    return(str(annee))



class IsDossier(models.Model):
    _name = 'is.dossier'
    _description = "Dossier"
    _order = 'numaff desc'
    _rec_name = 'numaff'


    @api.multi
    def _get_numaff(self):
        prefix = _get_prefix_annee()+'A'
        dossiers=self.env['is.dossier'].search([('numaff','like',prefix)],order="numaff desc",limit=1)
        numaff=1
        for dossier in dossiers:
            numaff = int(dossier.numaff[-3:])
            numaff+=1
        numaff=prefix+('000'+str(numaff))[-3:]
        return numaff

    numaff               = fields.Char("Dossier", required=True, index=True, default=lambda self: self._get_numaff())
    nom                  = fields.Char("Nom", required=True)
    description_succinte = fields.Text("Description succinte")
    adresse1             = fields.Char("Adresse 1")
    adresse2             = fields.Char("Adresse 2")
    codepostal           = fields.Char("Code postal")
    lieu                 = fields.Char("Ville")
    numconcours          = fields.Char("Numéro de concours")
    m_ouvrage_id         = fields.Many2one('res.partner', u"Maitre d'ouvrage", domain=[('is_company','=',True)])
    m_oeuvre_id          = fields.Many2one('res.partner', u"Maitre d'oeuvre" , domain=[('is_company','=',True)])
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
    state                = fields.Selection([
            ('en cours' ,'En cours'),
            ('termine'  ,'Terminé'),
            ('abandonne','Abandonné'),
        ],"Etat", default="en cours")

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

    name   = fields.Char(u"Traitance", required=True, index=True)
    code   = fields.Char(u"Code")
    active = fields.Boolean(u"Active", default=True)


class IsDossierContrat(models.Model):
    _name = 'is.dossier.contrat'
    _description = u"Contrat"
    _order = 'name desc'

    @api.depends('detail_ids')
    def _compute_restant_ht(self):
        for obj in self:
            restant_ht    = 0
            facturable_ht = 0
            for line in obj.detail_ids:
                restant_ht    += line.montant_ht-line.montant_ht*line.facture/100.0
                if line.a_facturer>line.facture:
                    facturable_ht += line.montant_ht*(line.a_facturer-line.facture)/100.0
            obj.restant_ht    = restant_ht
            obj.facturable_ht = facturable_ht

    @api.multi
    def _get_numcontrat(self):
        context = self._context
        numcontrat=''
        if 'active_id' in context:
            dossier_id = context['active_id']
            dossiers=self.env['is.dossier'].search([('id','=',dossier_id)])
            for dossier in dossiers:
                numaff = dossier.numaff
                prefix = numaff.replace('A','CT')
                dossiers=self.env['is.dossier.contrat'].search([('dossier_id','=',dossier_id)])
                nb = len(dossiers) + 1
                numcontrat = prefix+'-'+str(nb)
        return numcontrat


    name          = fields.Char(u"Numero de contrat", required=True, index=True, default=lambda self: self._get_numcontrat())
    signe         = fields.Selection([('oui','Oui'),('non','Non')],"Signé")
    dossier_id    = fields.Many2one('is.dossier', u"Dossier", index=True, required=True, ondelete='cascade')
    client_id     = fields.Many2one('res.partner', u"Client", index=True)
    description   = fields.Char(u"Description du contrat")
    notes         = fields.Text(u"Notes")
    condreglement = fields.Text(u"Condition de règlement")
    delaipaiement = fields.Text(u"Délai de paiement")
    date          = fields.Date(u"Date de signature")
    refclient     = fields.Char(u"N°Commande client", help=u"Utilisé pour les marchés publiques")
    num_marche    = fields.Char(u"N°Marché"    , help=u"Utilisé pour les marchés publiques")
    #bon_commande  = fields.Char(u"N°Commande"  , help=u"Utilisé pour les marchés publiques")
    code_service  = fields.Char(u"Code service", help=u"Utilisé pour les marchés publiques")
    traitance_id  = fields.Many2one('is.dossier.contrat.traitance', u"Traitance", index=True)
    invoice_ids   = fields.One2many('account.invoice', 'is_contrat_id', u'Factures', domain=[('state','not in',['cancel'])], readonly=True)
    detail_ids    = fields.One2many('is.dossier.contrat.detail', 'contrat_id', u'Détail')
    restant_ht    = fields.Float(u"Restant HT"   , digits=(14,2), compute='_compute_restant_ht', readonly=True, store=True)
    facturable_ht = fields.Float(u"Facturable HT", digits=(14,2), compute='_compute_restant_ht', readonly=True, store=True)
    heure_ids     = fields.One2many('is.salarie.heure', 'contrat_id', u'Heures', readonly=True)


# TODO : La numérotation automatique pose problème à l'importation et pour faire le lien avec les factures si modification de celle-ci
#    @api.multi
#    def write(self, vals):
#        res=super(IsDossierContrat, self).write(vals)
#        for obj in self:
#            numligne=10
#            for line in obj.detail_ids:
#                line.numligne = numligne
#                numligne+=10
#        return res


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






    @api.multi
    def generer_facture_action(self, vals):
        for obj in self:

            #** Recherche si il y a des lignes a facturer **********************
            test=False
            for line in obj.detail_ids:
                if line.a_facturer>line.facture:
                    test=True
            if test==False:
                raise Warning(u"Aucune ligne à facturer sur ce contrat")
            #*******************************************************************


            #** Recherche du numéro de facture *********************************
            prefix = _get_prefix_annee()+'FC'
            filtre=[
                ('number','like',prefix),
            ]
            invoices = self.env['account.invoice'].search(filtre,limit=1,order='number desc')
            suffix=1
            for invoice in invoices:
                suffix = int(invoice.number[-3:])+1
            suffix = ('000'+str(suffix))[-3:]
            number  = prefix+suffix
            #*******************************************************************


            #** Création entête facture ****************************************
            vals={
                'name'              : number,
                'origin'            : obj.name,
                'move_name'         : number,
                'number'            : number,
                'partner_id'        : obj.client_id.id,
                'is_contrat_id'     : obj.id,
                'fiscal_position_id': 1,
                'type'              : 'out_invoice',
                'state'             : 'draft',
            }
            invoice=self.env['account.invoice'].create(vals)
            invoice_id = invoice.id
            #*******************************************************************

            #** Création lignes du contrat *************************************
            for line in obj.detail_ids:
                quantity = line.a_facturer/100.0
                vals={
                    'invoice_id': invoice_id,
                    'is_contrat_detail_id': line.id,
                    'product_id': 1,
                    'name'      : line.texte,
                    'quantity'  : quantity,
                    'price_unit': line.montant_ht,
                    'account_id': 622, #701100
                }
                invoice_line=self.env['account.invoice.line'].create(vals)
                line_res = invoice_line.uptate_onchange_product_id()
                vals={
                    'name'      : line.texte,
                    'price_unit': line.montant_ht,
                }
                invoice_line.write(vals)
            #*******************************************************************


            #** Ajout des factures réalisées ***********************************
            filtre=[
                ('is_contrat_id','=',obj.id),
                ('date_invoice','<=',datetime.date.today()),
                ('state','not in',['cancel']),
                ('id','!=',invoice_id),
            ]
            factures = self.env['account.invoice'].search(filtre,order='date_invoice')
            for facture in  factures:
                vals={
                    'invoice_id'   : invoice_id,
                    'product_id'   : 2,
                    'name'         : facture.number,
                    'quantity'     : 1,
                    'price_unit'   : -facture.amount_untaxed,
                    'account_id'   : 622, #701100
                    'is_invoice_id': facture.id,
                }
                invoice_line=self.env['account.invoice.line'].create(vals)
                line_res = invoice_line.uptate_onchange_product_id()
                vals={
                    'name'      : facture.number,
                    'price_unit': -facture.amount_untaxed,
                }
                invoice_line.write(vals)
            #*******************************************************************


            #** Recalcul de la TVA et validation de la facture *****************
            res_validate = invoice.compute_taxes()
            try:
                res_validate = invoice.action_invoice_open()
            except:
                continue
            #*******************************************************************

            obj._compute_restant_ht()


class IsDossierContratDetail(models.Model):
    _name = 'is.dossier.contrat.detail'
    _description = u"Détail Contrat"
    _order = 'contrat_id,numligne'
    _rec_name = 'numligne'


    @api.depends('montant1','montant2','montant3','montant4')
    def _compute_montant_ht(self):
        for obj in self:
            obj.montant_ht = obj.montant1 + obj.montant2 + obj.montant3 + obj.montant4


    @api.depends('a_facturer')
    def _compute_facture(self):
        cr = self._cr
        for obj in self:
            facture=0
            if obj.montant_ht>0 and obj.id:
                SQL="""
                    select max(ail.price_subtotal)
                    from account_invoice_line ail inner join account_invoice ai on ail.invoice_id=ai.id
                    where 
                        ail.is_contrat_detail_id="""+str(obj.id)+""" and
                        ai.state not in ('cancel')
                """
                cr.execute(SQL)
                result = cr.fetchall()
                montant=0
                for row in result:
                    montant = row[0] or 0
                facture=100.0*montant/obj.montant_ht
            obj.facture=facture


    contrat_id  = fields.Many2one('is.dossier.contrat', 'Contrat', required=True, ondelete='cascade')
    numligne    = fields.Integer(u"Ligne")
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

    avancement  = fields.Float(u"% avancement")
    nota        = fields.Char(u"Nota")
    facturable  = fields.Selection([('oui','Oui'),('non','Non')],"Facturable", default='oui')
    a_facturer  = fields.Float(u"% à facturer")
    facture     = fields.Float(u"% facturé", compute='_compute_facture', readonly=True, store=False)
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
    _order = 'ordre,code'
    _rec_name = 'code'

    ordre       = fields.Char(u"Ordre"      , required=True, index=True, default='x')
    code        = fields.Char(u"Code"       , required=True, index=True)
    description = fields.Char(u"Description", required=True, index=True)


class IsSalarieHeure(models.Model):
    _name = 'is.salarie.heure'
    _description = u"Heures des salariés"
    _order = 'date_travaillee desc'
    _rec_name = 'date_travaillee'

    date_travaillee = fields.Date(u"Date travaillée", required=True, index=True, default=lambda *a: fields.Date.today())
    user_id         = fields.Many2one('res.users', 'Utilisateur', required=True, default=lambda self: self.env.user)
    login           = fields.Char(u"Login")
    contrat_id      = fields.Many2one('is.dossier.contrat', 'Contrat', required=True, ondelete='cascade')
    nb_heures       = fields.Float(u"Nb heures")
    note            = fields.Char(u"Note")
    id_heures       = fields.Integer(u"id_heures", index=True)


class IsDeclarationMAF(models.Model):
    _name = 'is.declaration.maf'
    _description = u"Déclaration MAF"

    name          = fields.Char(u"Année", required=True, index=True)
    type_document = fields.Selection([('maf',u'Déclaration MAF'),('dget','DGET')],"Type de document", default='maf')

    @api.multi
    def getCodeAssurance(self,code_id):
        cr = self._cr
        SQL="SELECT code,ordre FROM is_dossier_code_assurance where id="+str(code_id)
        cr.execute(SQL)
        rows = cr.fetchall()
        code=''
        ordre=''
        for row in rows:
            code  = row[0]
            ordre = row[1]
        return code, ordre


    @api.multi
    def get_contrats(self,obj):
        cr = self._cr
        SQL="""
            select 
                idcd.codass1_id,
                idcd.codass2_id,
                idcd.codass3_id,
                idcd.codass4_id,
                idcd.montant1,
                idcd.montant2,
                idcd.montant3,
                idcd.montant4,
                ai.name,
                ail.sequence,
                idc.name,
                id.numaff,
                rp.name,
                ail.is_contrat_detail_id,
                ail.price_subtotal,
                (ail.quantity-ail.is_deja_facture),
                ail.is_invoice_id
            from account_invoice_line ail inner join account_invoice             ai on ail.invoice_id=ai.id
                                          inner join is_dossier_contrat         idc on ai.is_contrat_id=idc.id
                                          inner join is_dossier_contrat_detail idcd on ail.is_contrat_detail_id=idcd.id
                                          inner join res_partner                 rp on ai.partner_id=rp.id
                                          inner join is_dossier                  id on idc.dossier_id=id.id
            where 
                ai.date_invoice>='"""+str(obj.name)+"""-01-01' and
                ai.date_invoice<='"""+str(obj.name)+"""-12-31'
            order by ai.name,ail.sequence
        """
        cr.execute(SQL)
        rows = cr.fetchall()
        nb=len(rows)
        r={}
        for row in rows:
            contrat = row[10]
            if contrat not in r:
                r[contrat]={}
            qty = row[15]
            if qty:
                if row[0]:
                    if row[0] not in r[contrat]:
                        r[contrat][row[0]]=0
                    r[contrat][row[0]]+=row[4]*qty
                if row[1]:
                    if row[1] not in r[contrat]:
                        r[contrat][row[1]]=0
                    r[contrat][row[1]]+=row[5]*qty
                if row[2]:
                    if row[2] not in r[contrat]:
                        r[contrat][row[2]]=0
                    r[contrat][row[2]]+=row[6]*qty
                if row[3]:
                    if row[3] not in r[contrat]:
                        r[contrat][row[3]]=0
                    r[contrat][row[3]]+=row[7]*qty
        keys=sorted(r.keys(), reverse=True)
        total=0
        res=[]
        recap={}
        for k in keys:
            lines={}
            for code_id in r[k]:
                montant = r[k][code_id]
                code,ordre = self.getCodeAssurance(code_id)
                lines[ordre]=[code,montant]
            keys2=sorted(lines.keys(), reverse=False)
            for k2 in keys2:
                line    = lines[k2]
                code    = line[0].strip()
                montant = line[1]
                contrats = self.env['is.dossier.contrat'].search([('name','=',k)],order="name",limit=1)
                if contrats:
                    contrat=contrats[0]
                    traitance = contrat.traitance_id.code or ''
                    cle=code+' '+traitance
                    if cle not in recap:
                        recap[cle]=0
                    recap[cle]+=montant
                    vals={
                        'contrat'  : contrat,
                        'code'     : code,
                        'traitance': traitance,
                        'montant'  : montant,
                    }
                    res.append(vals)
                    total+=r[k][code_id]
        keys=sorted(recap.keys(), reverse=False)
        recap2=[]
        for k in keys:
            recap2.append([k,recap[k]])
        return [res,recap2]


class IsConcours(models.Model):
    _name = 'is.concours'
    _description = u"Concours"
    _order = 'numconcours desc'
    _rec_name = 'numconcours'

    @api.multi
    def _get_numconcours(self):
        prefix = _get_prefix_annee()+'CO'
        rows=self.env['is.concours'].search([('numconcours','like',prefix)],order="numconcours desc",limit=1)
        numconcours=1
        for row in rows:
            numconcours = int(row.numconcours[-3:])
            numconcours+=1
        numconcours=prefix+('000'+str(numconcours))[-3:]
        return numconcours

    numconcours    = fields.Char(u"Numero de concours", required=True, index=True, default=lambda self: self._get_numconcours())
    organisme_id   = fields.Many2one('res.partner', u"Organisme", domain=[('is_company','=',True)])
    nom            = fields.Char(u"Nom du concours")
    libelle_exacte = fields.Text(u"Libelle exacte")
    lieu           = fields.Char(u"Lieu")
    dateparution   = fields.Date(u"Date de parution")
    daterendu      = fields.Date(u"Date rendu")
    journal        = fields.Char(u"Journal")
    lienannonce    = fields.Char(u"Lien annonce")
    qui_ids        = fields.One2many('is.concours.qui', 'concours_id', u'Equipes')


class IsConcoursQui(models.Model):
    _name = 'is.concours.qui'
    _description = u"Concours Qui"
    _order = 'nom'
    _rec_name = 'nom'

    concours_id  = fields.Many2one('is.dossier.contrat', 'Concours', required=True, ondelete='cascade')
    nom          = fields.Char(u"Nom", required=True, index=True)
    dateenvoi    = fields.Date(u"Date d'envoi")
    retenu       = fields.Selection([('oui','Oui'),('non','Non')],"Gagné" , default='non')
    gagne        = fields.Selection([('oui','Oui'),('non','Non')],"Retenu", default='non')
    equipes      = fields.Text(u"Equipes")


