from openerp.osv import osv,fields
from datetime import date
from openerp.tools.translate import _

class purchase_order(osv.osv):
	_name = "purchase.order"
	_inherit = "purchase.order"

	_columns = {
		'lote_id': fields.many2one('elote.lote','Lote',required=True,domain=[('state','=','open')],
                             states={'confirmed':    [('readonly', True)],
                                     'approved':     [('readonly', True)],
                                     'consolidated': [('readonly', True)],
                                     'not_valid':    [('readonly', True)],
                                     'in_process':   [('readonly', True)],
                                     'dispatched':   [('readonly', True)],
                                     'received':     [('readonly', True)]}),
		}

        _defaults = {
            'lote_id': lambda self, cr, uid, context: (self.pool.get('elote.lote').search(cr, uid, [('state','=','open')]) + [False])[0],
        }

	def _check_valid_lote(self, cr, uid, ids, context=None):
		obj = self.browse(cr, uid, ids[0], context=context)
		if not obj.lote_id.id:
			return False
		lote_obj = self.pool.get('elote.lote').browse(cr, uid, obj.lote_id.id, context=context)
		# Valida el estado
		if obj.state <> 'open':
			return False
		# Valida la fecha
		today = date.today()
		if (str(today) < lote_obj.date_start) or (str(today) > lote_obj.date_end):
			return False
		# Valida que el usuario pueda realizar la operacion
		invalid_user = True
		for user in lote_obj.user_ids:
			if obj.create_uid.id == user.id:
				invalid_user = False
		if invalid_user:
			return False

		# Valida que el producto pertenezca al lote
		invalid_product = True
		for line in obj.order_line:
		    for product_lote in self.pool.get('product.product').search(cr, uid, [], context={'search_default_elote_id': obj.order_id.lote_id.id}):
                            if product_lote == line.product_id.id:
                                    invalid_product = False

		# Valida que el producto pertenezca al lote
		invalid_product = False
		for line in obj.order_line:
                    product_lote_ids = self.pool.get('product.product').search(cr, uid, [('id','=',line.product_id.id)], context={'search_default_elote_id': obj.order_id.lote_id.id})
                    invalid_product = not product_lote_ids
                    if invalid_product:
                        message_id = self.message_post(cr, uid, [so.id],
                                                       subject=_('Request action'),
                                                       body=_('The product %s is required for this lote.') % (line.product_id.name))

		if invalid_product:
                    return False

        	return True

        def create(self, cr, uid, vals, context=None):
		lote_id = self.pool.get('elote.lote').search(cr,uid,[('state','=','open')])
		if not lote_id:
                        raise osv.except_osv('Error!', 'No hay lotes abiertos para procesar.')

		vals['lote_id'] = lote_id[0]
		user_obj = self.pool.get('res.users').browse(cr,uid,uid,context=context)
		vals['dest_address_id'] = user_obj.partner_id.id
		
		if not vals['lote_id']:
                        raise osv.except_osv('Error!', 'No hay lotes abiertos para procesar.')
		valid_user = False
		obj = self.pool.get('elote.lote').browse(cr, uid, lote_id, context=context)
		for user in obj[0].user_ids:
			if user.id == uid:
				valid_user = True
				break
		if not valid_user:
                        raise osv.except_osv('Error!', 'El usuario no se encuentra habilitado para procesar lotes.')
			
        	return super(purchase_order, self).create(cr, uid, vals, context=context)
	

purchase_order()


class purchase_order_line(osv.osv):
	_name = "purchase.order.line"
	_inherit = "purchase.order.line"

	def _check_lotes(self, cr, uid, ids, context=None):
            assert len(ids) == 1, "Only works by one line"
            obj = self.browse(cr, uid, ids[0], context=context)
            r = len(self.pool.get('product.product').search(cr, uid,
                                                               [('id','=',obj.product_id.id)],
                                                               context={'search_default_elote_id': obj.order_id.lote_id.id})
                      )
            if r != 1:
                import pdb; pdb.set_trace()
            return r == 1

	_constraints = [
        	(_check_lotes, 'Product should be included in lote say line', ['product_id']),
    	]

purchase_order_line()

