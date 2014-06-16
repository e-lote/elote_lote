from openerp.osv import osv,fields
from datetime import date

class purchase_order(osv.osv):
	_name = "purchase.order"
	_inherit = "purchase.order"

	_columns = {
		'lote_id': fields.many2one('elote.lote','Lote'),
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

		# Valida que el usuario pueda realizar la operacion
		invalid_product = True
		for line in obj.order_line:
			for product_lote in lote_obj.product_ids:
				if product_lote.id == line.product_id.id:
					invalid_product = False
		if invalid_product:
			return False


        	return True

	#_constraints = [
        #	(_check_valid_lote, 'Invalid lote.', ['lote_id']),
    	#]

        def create(self, cr, uid, vals, context=None):
		# sequence_id = self.pool.get('ir.sequence').search('name','=','E-Lote')
		#sequence_id = self.pool.get('ir.sequence').search('prefix','=','LOT')
		#if not sequence_id:
                #        raise osv.except_osv(_('Error!'), _('Please define a sequence for lotes.'))
		vals['lote_id'] = self.pool.get('elote.lote').search(cr,uid,[('state','=','open')])[0]
		if not vals['lote_id']:
                        raise osv.except_osv('Error!', 'No hay lotes abiertos para procesar.')
			
        	return super(purchase_order, self).create(cr, uid, vals, context=context)
	

purchase_order()

"""
class purchase_order_line(osv.osv):

	def _check_dates(self, cr, uid, ids, context=None):
		obj = self.browse(cr, uid, ids[0], context=context)
		if obj.date_start > obj.date_end:
			return False
        	return True

	_constraints = [
        	(_check_dates, 'Start date should be less than end date.', ['product_id']),
    	]

purchase_order_line()


class elote_lote(osv.osv):
	_name = "elote.lote"
	_description = "Lot Administration class"

	_columns = {
		'name': fields.char('Name',size=32),
		'date_start': fields.date('Start Date'),
		'date_end': fields.date('Start End'),
		'state': fields.selection((('draft','Draft'),('in_process','In Process'),('done','Done')),'State'),
	        'product_ids': fields.many2many('product.product', 'product_lote_rel', 'lote_id', 'product_id', 'Products'),
	        'user_ids': fields.many2many('res.users', 'res_user_rel', 'lote_id', 'user_id', 'Users'),
		}

	_defaults = {
		'state': 'draft'
		}

	def _check_dates(self, cr, uid, ids, context=None):
		obj = self.browse(cr, uid, ids[0], context=context)
		if obj.date_start > obj.date_end:
			return False
        	return True

	_constraints = [
        	(_check_dates, 'Start date should be less than end date.', ['date_start','date_end']),
    	]

elote_lote()

"""
