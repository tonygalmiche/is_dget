# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
from datetime import date, datetime


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
            montant_hors_revision = obj.amount_untaxed - montant
            obj.is_montant_hors_revision = montant_hors_revision
            if obj.type=="out_refund":
                obj.is_montant_hors_revision_signe = - montant_hors_revision
            else:
                obj.is_montant_hors_revision_signe = montant_hors_revision

    is_contrat_id            = fields.Many2one('is.dossier.contrat', u'Contrat', index=True)
    is_total_contrat_ht      = fields.Float(u"Total contrat HT"     , digits=(14,2), compute='_compute_total_contrat_ht', readonly=True, store=False)
    is_montant_revision      = fields.Float(u"Montant révision"     , digits=(14,4), compute='_compute_montant_revision', readonly=True, store=True)
    is_montant_hors_revision = fields.Float(u"Montant hors révision", digits=(14,4), compute='_compute_montant_revision', readonly=True, store=True)
    is_montant_hors_revision_signe = fields.Float(u"Montant hors révision signé", digits=(14,4), compute='_compute_montant_revision', readonly=True, store=True)
    is_dossier_id            = fields.Many2one('is.dossier', u"Dossier"       , compute='_compute_dossier_id'      , readonly=True, store=True, index=True)
    is_tva_id                = fields.Many2one('is.tva', u'TVA')
    is_date_update_facture   = fields.Datetime("Date mise à jour déjà facturé")
    is_facture_payee         = fields.Selection([('oui','Oui'),('non','Non')],"Payée", default="non", required=True)


    @api.multi
    def name_get(self):
        result = []
        for obj in self:
            #result.append((obj.id, str(obj.numaff)+u' - '+str(obj.nom)))
            result.append((obj.id, str(obj.name)))
        return result


    @api.multi
    def _get_report_base_filename(self):
        if self.type in ['out_invoice','in_invoice']:
            prefix = "Facture"
        else:
            prefix = "Avoir"
        date = self.date_invoice.strftime('%y%m%d')
        name="%s_%s"%(date,self.number)
        return name

        # return  self.type == 'out_invoice' and self.state == 'draft' and _('Draft Invoice') or \
        #         self.type == 'out_invoice' and self.state in ('open','in_payment','paid') and _('Invoice - %s') % (self.number) or \
        #         self.type == 'out_refund' and self.state == 'draft' and _('Credit Note') or \
        #         self.type == 'out_refund' and _('Credit Note - %s') % (self.number) or \
        #         self.type == 'in_invoice' and self.state == 'draft' and _('Vendor Bill') or \
        #         self.type == 'in_invoice' and self.state in ('open','in_payment','paid') and _('Vendor Bill - %s') % (self.number) or \
        #         self.type == 'in_refund' and self.state == 'draft' and _('Vendor Credit Note') or \
        #         self.type == 'in_refund' and _('Vendor Credit Note - %s') % (self.number)


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
            print("####",obj)
            for line in obj.invoice_line_ids:
                if line.product_id:
                    line.account_id = obj.is_tva_id.account_id.id
                    line.invoice_line_tax_ids = [(6,0,[obj.is_tva_id.tax_id.id])]
            obj.compute_taxes()
        return True

    def update_deja_facture_recursif(self, deja_factures, visites, now):
        """
        Parcours d'arbre "bottom-up" (on parcourt le fond avant de changer la racine)
        avec pour objectif de calculer "réellement facturé" et "deja_facture" pour chaque noeud

        --- Idée générale ---
        Case de base 1: on a déjà été visité
        Case de base 2: on a pas de factures liées
        Cas général:
        -- 1. Calculer récursivement les "déjà factures" et "visites" des factures filles d'abord 
        -- 2. Traiter la facture courante
        -- 3. Update "déjà factures" et "visites" pour le futur

        --- Remarques ---
        Si c'est un avoir:
        -- 1. Diminuer la quantité déjà facturé "du futur" (parce qu'on enlève quelque chose qui était facturé)
        -- 2. Réellement facturé est négatif (on rend des sous)
        Si c'est une facture classique:
        -- 1. Augmenter la quantité déjà facturé "du futur"
        -- 2. Réellement facturé est positif
        Conclusion: 
        -- Le signe de réellement facturé dépend de si on doit donner des sous ou en reprendre
        -- reellement_facture = quantité - déjà facturé
        -- deja_facture du futur = line.is_reellement_facture + line.is_deja_facture
        """
        for obj in self:
            
            # ----------------- Initialization -----------------
            factures = []  # liste des factures dans la facture courante
            services = []  # liste des services dans la facture courante

            # on parcourt chaque ligne
            for line in obj.invoice_line_ids:
                # retrouver tous les services
                if line.is_contrat_detail_id:
                    services.append(line)
                # retrouver toutes les factures
                if line.is_invoice_id and line.is_invoice_id.state not in ['draft','cancel']:
                    factures.append(line)
                if line.is_invoice_id and line.is_invoice_id.state in ['draft','cancel']:
                    print("line is ", line.is_invoice_id.state)


            # ----------------- Cas de base ---------------------
            # Case de base 1: on a déjà été visité
            if obj in visites:
                return deja_factures, visites

            # case de base 2: on a pas de factures liées
            if obj not in visites and factures == []:
                #print('cas de base 2: pas de facture enfant')
                for line in services:

                    # mettre à jour odoo, la colonne reellement factures
                    line.is_reellement_facture = line.quantity
                    line.is_montant_reellement_facture = line.is_reellement_facture * abs(line.price_unit)

                    # mettre à jour odoo, la colonne déjà factures
                    line.is_deja_facture = 0.

                    # mettre à jour la liste des choses déjà facturées avec celles facturées dans la facture courante
                    deja_factures[line.is_contrat_detail_id] = line.is_reellement_facture
                # mettre à jour le "now"
                obj.is_date_update_facture = now
                # rajouter la facture courante come visitee
                visites.append(obj)
                return deja_factures, visites

            # ------------- Cas général: traitement des fils ------------------
            # Cas général: 
            if obj not in visites and factures:
                #print("cas général avec %d fils et %d services " %(len(factures), len(services)))
                # Récupérer les déjà factures et visites des fils un à un 
                for line in factures:
                    deja_factures, visites = line.is_invoice_id.update_deja_facture_recursif(deja_factures, visites, now)
                    line.is_deja_facture = line.quantity
                    line.reellement_facture = 0.
                # Mettre à jour la facture courante
                for line in services:
                    # Mettre à jour odoo en utilisant les resultat des factures enfants. 
                    if line.is_contrat_detail_id in deja_factures:
                        line.is_deja_facture = deja_factures[line.is_contrat_detail_id]
                    # Sinon mettre à 0
                    else:
                        line.is_deja_facture = 0
                    line.is_reellement_facture = line.quantity - line.is_deja_facture
                    line.is_montant_reellement_facture = line.is_reellement_facture * abs(line.price_unit)
                    # mettre à jour la liste des choses des "futurs" déjà facturées 
                    # comme la somme des déjà facturées + du reellement facturé de cette facture
                    deja_factures[line.is_contrat_detail_id] = line.is_reellement_facture + line.is_deja_facture

                # mettre à jour le "now"
                obj.is_date_update_facture = now
                # Marquer cette facture comme étant visitée
                visites.append(obj)
            return deja_factures, visites

    # def update_deja_facture_recursif(self, now,niveau, sens, res):
    #     for obj in self:
    #         if now!=obj.is_date_update_facture:
    #             print(niveau*" -", obj.name)
    #             for line in obj.invoice_line_ids:
    #                 line_sens=sens
    #                 if line.price_unit<0:
    #                     line_sens=-line_sens
    #                 if obj.type=="out_refund":
    #                     line_sens=-line_sens
    #                 if line.is_invoice_id and line.is_invoice_id.state not in ['draft','cancel']:
    #                     res=line.is_invoice_id.update_deja_facture_recursif(now,niveau+1,line_sens,res)
    #             #     if line.is_contrat_detail_id:
    #             #         phase_id = line.is_contrat_detail_id.phase_id
    #             #         if phase_id not in res:
    #             #             res[phase_id]=0
    #             #         res[phase_id]+=line_sens*(line.quantity - line.is_deja_facture)



    #         else:
    #             print(niveau*" -", obj.name, "OK")
    #             # #** Retourner ce qui est reelement facturé sans MAJ ***********
    #             # for line in obj.invoice_line_ids:
    #             #     line_sens=sens
    #             #     if line.price_unit<0:
    #             #         line_sens=-line_sens
    #             #     if obj.type=="out_refund":signe_line******


                


                # on traite la queue ensuite en taillant les branches déjà visitées
            

            # if now!=obj.is_date_update_facture:
            #     print(niveau*" -", obj.name)

            # for line in obj.invoice_line_ids:

            #     line_sens=sens
            #     if line.price_unit<0:
            #         line_sens=-line_sens
            #     if obj.type=="out_refund":
            #         line_sens=-line_sens


            #     #if now!=obj.is_date_update_facture:
            #     if line.is_invoice_id and line.is_invoice_id.state not in ['draft','cancel']:
            #         res=line.is_invoice_id.update_deja_facture_recursif(now,niveau+1,line_sens,res)


            #     if line.is_contrat_detail_id:
            #         phase_id = line.is_contrat_detail_id.phase_id
            #         #print(obj.name,res)
            #         if phase_id not in res:
            #             res[phase_id]=0
            #         #quantity  = line.quantity
            #         res[phase_id]+=line_sens*(line.quantity) #-line.is_deja_facture)
            # else:
            #     for line in obj.invoice_line_ids:
            #        if line.is_contrat_detail_id:
            #             phase_id = line.is_contrat_detail_id.phase_id
            #             #print(obj.name,res)
            #             if phase_id not in res:
            #                 res[phase_id]=0
            #             #quantity  = line.quantity
            #             res[phase_id]+=(line.quantity -line.is_deja_facture) #-line.is_deja_facture)



            #obj.is_date_update_facture = now
            # #print(obj.name,res)
            # for res_line in res:
            #     for invoice_line in obj.invoice_line_ids:
            #         if res_line==invoice_line.is_contrat_detail_id.phase_id:
            #             deja_facture =  invoice_line.quantity - res[res_line]
            #             print(niveau*" -", obj.name,"- \t facturé =",res_line.txt_phase,res[res_line], "\t qt =",invoice_line.quantity,"\t deja_facture =",deja_facture)
            #             invoice_line.is_deja_facture =deja_facture



            #return res


    #                 invoices.append(line.is_invoice_id.name)
    #             txt_phase = line.is_contrat_detail_id.phase_id.txt_phase
    #             quantity  = line.quantity

    #             line_sens=sens
    #             if line.price_unit<0:
    #                 line_sens=-line_sens
    #             if invoice.type=="out_refund":
    #                 line_sens=-line_sens
    #             vals={
    #                 "niveau"      : niveau,
    #                 "invoice_name": invoice.name,
    #                 "invoice_type": invoice.type,
    #                 "is_contrat_detail_id": line.is_contrat_detail_id,
    #                 "txt_phase"   : txt_phase,
    #                 "price_unit"  : line.price_unit,
    #                 "sens"        : line_sens,
    #                 "quantity"    : quantity,
    #             }
    #             lines.append(vals)
    #             if line.is_invoice_id and line.is_invoice_id.state not in ['draft','cancel']:
    #                 res = obj.get_invoice_line_recursif(compteur+1, niveau+1, lines, line_sens, line.is_invoice_id, invoices)
    #                 lines    = res.get("lines"   , [])
    #                 compteur = res.get("compteur", 0)
    #                 invoices = res.get("invoices", [])
    #         res={
    #             "lines"   : lines,
    #             "compteur": compteur,
    #             "invoices": invoices,
    #         }
    #         return res

    @api.multi
    def update_deja_facture_action(self):
        # récupérer le nombre de factures sélectionnées
        n_factures = len(self)
        # Traiter par paquet de 1000 factures max à cause de pb de mémoire
        N_max = 1000
        i_start = 0
        while i_start < n_factures:
            now=datetime.now()
            # Se souvenir de toutes les factures visitées
            deja_factures = {}
            visites = []
            # parcourir les factures
            for i,obj in enumerate(self[i_start: i_start+N_max]):
                t_start = datetime.now()
                deja_factures, visites = obj.update_deja_facture_recursif(deja_factures, visites, now)
                t_end = datetime.now()
                t = (t_end - t_start).total_seconds()
                print(" --- facture %d / %d --- %s --- %.6f sec --- " %(i+1, min(N_max, n_factures), obj.name, t))
            t_end_tot = datetime.now()
            print("Mise à jour de toutes les factures en %.6f secondes" %((t_end_tot - now).total_seconds()))
            i_start += N_max


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    #_order = 'is_contrat_detail_id'
    _order = 'sequence,id'

    is_contrat_detail_id          = fields.Many2one('is.dossier.contrat.detail', 'Ligne Contrat', index=True)
    is_invoice_id                 = fields.Many2one('account.invoice', 'Facture liée')
    is_deja_facture               = fields.Float("Déjà facturé", digits=(14,6))
    is_reellement_facture         = fields.Float("Réellement facturé", digits=(14,6))
    is_montant_reellement_facture = fields.Float("Montant réellement facturé", digits=(14,2))

    @api.multi
    def uptate_onchange_product_id(self):
        for obj in self:
            obj._onchange_product_id()
            #obj._compute_price()
            #obj._set_taxes()
            obj.invoice_id.compute_taxes()

        return True

