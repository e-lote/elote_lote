from openerp.osv import osv,fields
from datetime import date

class elote_lote(osv.osv):
	_name = "elote.lote"
	_description = "Lot Administration class"

	_columns = {
		'name': fields.char('Name',size=32),
		'sequence_nbr': fields.char('Sequence Nbr',size=32),
		'date_start': fields.date('Start Date'),
		'date_end': fields.date('Start End'),
		'state': fields.selection((('draft','Borrador'),('open','Abierto'),('in_process','Proceso'),('close','Cierre'),('done','Realizado')),'State'),
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

        def write(self, cr, uid, ids, vals, context=None):
		# sequence_id = self.pool.get('ir.sequence').search('name','=','E-Lote')
		#sequence_id = self.pool.get('ir.sequence').search('prefix','=','LOT')
		#if not sequence_id:
                #        raise osv.except_osv(_('Error!'), _('Please define a sequence for lotes.'))
		if 'state' in vals.keys():
			if vals['state'] == 'open':
				lote_ids = self.search(cr,uid,[('state','=','open')])
				if len(lote_ids) > 0:
        		                raise osv.except_osv('Error!', 'Ya existen lotes en estado open.')
			
        	return super(elote_lote, self).write(cr, uid, ids, vals, context=context)

        def create(self, cr, uid, vals, context=None):
		# sequence_id = self.pool.get('ir.sequence').search('name','=','E-Lote')
		#sequence_id = self.pool.get('ir.sequence').search('prefix','=','LOT')
		#if not sequence_id:
                #        raise osv.except_osv(_('Error!'), _('Please define a sequence for lotes.'))
		vals['sequence_nbr'] = 'LOTE ' + str(date.today())
		lote_ids = self.search(cr,uid,[('state','=','open')])
		if len(lote_ids) > 1:
                        raise osv.except_osv('Error!', 'Ya existen lotes en estado open.')
			
        	return super(elote_lote, self).create(cr, uid, vals, context=context)
	
	
	_constraints = [
        	(_check_dates, 'Start date should be less than end date.', ['date_start','date_end']),
    	]

elote_lote()
