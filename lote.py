from openerp.osv import osv,fields
from datetime import date
from openerp.tools.translate import _

class product_product(osv.osv):
    _name = "product.product"
    _inherit = "product.product"

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        context = context or {}
        if context.get('search_default_elote_id'):
            args.append((('id', 'inselect',('select PP.id from product_product PP left join product_supplierinfo SI on (SI.product_tmpl_id = PP.product_tmpl_id) where SI.lote_id = %s',
                          context['search_default_elote_id']))))
        if context.get('search_default_partner_id'):
            args.append((('id', 'inselect',('select PP.id from product_product PP left join product_supplierinfo SI on (SI.product_tmpl_id = PP.product_tmpl_id) where SI.name = %s',
                          context['search_default_partner_id']))))
        return super(product_product, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)
product_product()

class product_supplierinfo(osv.osv):
    _name = "product.supplierinfo"
    _inherit = "product.supplierinfo"

    _columns = {
            'lote_id': fields.many2one('elote.lote', 'Lote'),
    }
product_supplierinfo()

class elote_lote(osv.osv):
    _name = "elote.lote"
    _description = "Lot Administration class"
    _inherit = [ 'mail.thread' ]

    def _count_all(self, cr, uid, ids, field_name, arg, context=None):
       return {
           obj.id: {
               'supplier_ids_count': len(obj.supplier_ids),
               'order_ids_count': len(obj.order_ids),
           }
           for obj in self.browse(cr, uid, ids, context=context)
       }

    _columns = {
            'name': fields.char('Name',size=32),
            'sequence_nbr': fields.char('Sequence Nbr',size=32),
            'date_start': fields.date('Start Date'),
            'date_end': fields.date('Start End'),
            'state': fields.selection((('draft','Borrador'),('open','Abierto'),('in_process','Proceso'),('close','Cierre'),('done','Realizado')),'State'),
            'user_ids': fields.many2many('res.users', 'res_user_rel', 'lote_id', 'user_id', 'Users'),
            'supplier_ids': fields.one2many('product.supplierinfo', 'lote_id', 'Supplier Info'),
            'supplier_ids_count': fields.function(_count_all, type='integer', string=_("Supplier Info Count"), multi='_count_all', store=False),
            'order_ids': fields.one2many('purchase.order', 'lote_id', 'Purchase Orders'),
            'order_ids_count': fields.function(_count_all, type='integer', string=_("Purchase Order Count"), multi='_count_all', store=False),
            }

    _defaults = {
            'state': 'draft'
            }

    def _check_dates(self, cr, uid, ids, context=None):
            obj = self.browse(cr, uid, ids[0], context=context)
            if obj.date_start > obj.date_end:
                    return False
            return True

    def write(self, cr, uid, ids, vals, context=None):
            if 'state' in vals.keys():
                    if vals['state'] == 'open':
                            lote_ids = self.search(cr,uid,[('state','=','open')])
                            if len(lote_ids) > 0:
                                    raise osv.except_osv('Error!', 'Ya existen lotes en estado open.')
                    
            return super(elote_lote, self).write(cr, uid, ids, vals, context=context)

    def create(self, cr, uid, vals, context=None):
            vals['sequence_nbr'] = 'LOTE ' + str(date.today())
            lote_ids = self.search(cr,uid,[('state','=','open')])
            if len(lote_ids) > 1:
                    raise osv.except_osv('Error!', 'Ya existen lotes en estado open.')
                    
            return super(elote_lote, self).create(cr, uid, vals, context=context)
    
    
    _constraints = [
            (_check_dates, 'Start date should be less than end date.', ['date_start','date_end']),
    ]


    def view_supplier_ids(self, cr, uid, ids, context=None):
        res_id = ids and ids[0] or False
        return {
            'name': _('Supplier Info'),
            'domain': [('lote_id', 'in', ids)],
            'res_model': 'product.supplierinfo',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_lote_id': %s}" % (res_id)
        }

    def view_order_ids(self, cr, uid, ids, context=None):
        res_id = ids and ids[0] or False
        return {
            'name': _('Purchase Orders'),
            'domain': [('lote_id', 'in', ids)],
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_lote_id': %s}" % (res_id)
        }

    def catalog_import(self, cr, uid, ids, context=None):
        return {
            'name': _('Catalog Import'),
            'res_model': 'elote.catalog_import',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': "{'default_lote_id': %s}" % (ids[0])
        }

elote_lote()
