# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import date
from openerp import netsvc
from StringIO import StringIO
import csv
import base64

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

def _n(value, force=False):
    value = value.strip()
    if value:
        return value
    elif force:
        raise RuntimeError, "Must set a valid string"
    else:
        return False

def _f(value, force=False):
    value = value.lower().strip().replace(',','.')
    try:
        return float(value)
    except:
        if force:
            raise RuntimeError, "'%s' is not a valid number" % value
        return False

def _c(value, force=False):
    value = value.lower().strip().replace(',','.').replace('$','')
    try:
        return float(value)
    except:
        if force:
            raise RuntimeError, "'%s' is not a valid currency" % value
        return False

class catalog_import(osv.osv_memory):
    _name = 'elote.catalog_import'
    _description = 'Catalog Import'

    _columns = {
        'data': fields.binary(string='Catalog File', required=True),
        'lote_id': fields.many2one('elote.lote', string='Lote', domain="[('state','=','open')]", required=True),
        'first_row_column': fields.boolean('1st Row Column Names'),
        'delimiter': fields.selection([('|','bar (|)'),(',','comma (,)')], string="Delimiter", required=True),
        'update_products': fields.boolean('Update products'),
        'update_supplierinfo': fields.boolean('Update supplier info'),
        'complete_dimensions': fields.boolean('Complete dimensiones'),
    }

    _defaults = {
        'lote_id': lambda self, cr, uid, context: (self.pool.get('elote.lote').search(cr, uid, [('state','=','open')]) + [False])[0],
        'first_row_column': True,
        'delimiter': '|',
    }

    def do_import(self, cr, uid, ids, context=None):
        partner_obj       = self.pool.get('res.partner')
        supplierinfo_obj  = self.pool.get('product.supplierinfo')
        user_obj          = self.pool.get('res.users')
        product_obj       = self.pool.get('product.product')
        product_tmpl_obj  = self.pool.get('product.template')
        product_category_obj = self.pool.get('product.category')
        # Dimensions.
        paper_colour_obj  = self.pool.get('product.paper_colour')
        colour_pages_obj  = self.pool.get('product.colour_pages')
        publishing_bs_obj = self.pool.get('product.publishing_bs')
        endsheets_obj     = self.pool.get('product.endsheets')
        weight_gsmpp_obj  = self.pool.get('product.weight.gsmpp')
        ribbons_obj       = self.pool.get('product.reibbons')
        edge_obj          = self.pool.get('product.edge')
        size_obj          = self.pool.get('product.size')
        colour_obj        = self.pool.get('product.colour')
        binding_obj       = self.pool.get('product.binding')
        language_obj      = self.pool.get('product.language')
        familia_obj       = self.pool.get('product.familia')
        categoria_obj     = self.pool.get('product.categoria')
        version_obj       = self.pool.get('product.version')
        sub_categoria_obj = self.pool.get('product.subcategoria')

        # Supplier info collector        
        si_ids = []

        for wiz in self.browse(cr, uid, ids):
            ss = StringIO(unicode(base64.b64decode(wiz.data), 'utf-8'))
            ireader = unicode_csv_reader(ss, delimiter=str(wiz.delimiter))

            # Ignore first line
            if wiz.first_row_column:
                s = ireader.next()
                if len(s) != 45:
                    raise osv.except_osv(_('Error!'), _("File must have 45 columns. You give %s columns") % (len(s)))

            # Storage for each purchase order for each partner
            vals = {}

            # Help functions
            def imp_process(obj, fil, update, values):
                fil = [ f for f in fil if f[-1] ]
                if not fil:
                    return False
                ids = obj.search(cr, uid, fil)
                if len(ids) == 1 and update:
                    values = { key: value for key, value in values.items() if value != False }
                    obj.write(cr, uid, ids[0], values)
                    return ids[0]
                elif len(ids) == 1 and not update:
                    return ids[0]
                elif len(ids) > 1:
                    return False
                return obj.create(cr, uid, values)

            def category_obj(obj, value, create=True, force=False):
                value = value.lower().strip()
                if value:
                    r = (obj.search(cr, uid, [('name', '=', value)]) + [False])[0] or (create and obj.create(cr, uid, { 'name': value }))
                elif force:
                    raise RuntimeError, "Need valid name for object '%s'" % (obj.description)
                else:
                    return False
                if r:
                    return r
                elif force:
                    raise RuntimeError, "No instance for object '%s' with name '%s'" % (obj.description, value)
                else:
                    return False

            # Read all lines
            for row in ireader:
                # Check column count
                if len(row) != 45:
                    raise osv.except_osv(_('Error!'), _("Line %s: File must have 45 columns. You give %s columns") %
                                         (ireader.line_num, len(row)))
                
                # Translate values
                partner_id = (partner_obj.search(cr, uid, ['|',('name','=',row[10]),('ref','=',row[10])])+
                              [False])[0]
                product_tmpl_id = imp_process(product_tmpl_obj,
                                              [('ean13','=',row[1])],
                                              wiz.update_products,
                                              {'publishing_bs': category_obj(publishing_bs_obj, row[0], create=wiz.complete_dimensions),
                                               'ean13': _n(row[1]),
                                               'ubs_code_prefix': _n(row[2]), 
                                               'ubs_code_no': _n(row[3]),
                                               'ubs_code_suffix': _n(row[4]),
                                               'language': category_obj(language_obj, row[5], create=wiz.complete_dimensions),
                                               'version': category_obj(version_obj, row[6], create=wiz.complete_dimensions),
                                               'categ_id': category_obj(product_category_obj, row[7], create=wiz.complete_dimensions),
                                               'categoria': category_obj(categoria_obj, row[8], create=wiz.complete_dimensions),
                                               'subcategoria': category_obj(sub_categoria_obj, row[9], create=wiz.complete_dimensions),
                                               # row[10] Supplier -> supplierinfo
                                               'tps_width': _f(row[11]),
                                               'tps_height': _f(row[12]),
                                               'image_area_width': _f(row[13]),
                                               'image_area_height': _f(row[14]),
                                               'maps_area_width': _f(row[15]),
                                               'maps_area_height': _f(row[16]),
                                               'maps_area_colored_end_pages': _f(row[17]),
                                               'maps_area_colored_section_pages': _f(row[18]),
                                               'paper_colour_pages': category_obj(paper_colour_obj, row[19], create=wiz.complete_dimensions),
                                               'paper_weight_pages': _f(row[20]),
                                               'paper_gsm_pp': _f(row[21]),
                                               'paper_colour': category_obj(paper_colour_obj, row[22], create=wiz.complete_dimensions),
                                               'bible_binding': category_obj(binding_obj, row[23], create=wiz.complete_dimensions),
                                               'bible_colour': category_obj(colour_obj, row[24], create=wiz.complete_dimensions),
                                               'bible_size': category_obj(size_obj, row[25], create=wiz.complete_dimensions),
                                               'endsheets': category_obj(endsheets_obj, row[26], create=wiz.complete_dimensions),
                                               'weight_gsm_pp': category_obj(weight_gsmpp_obj, row[27], create=wiz.complete_dimensions),
                                               'ribbons': _f(row[28]),
                                               'edge': category_obj(edge_obj, row[29], create=wiz.complete_dimensions),
                                               'ref': _n(row[42]),
                                               'name': _n(row[43]),
                                               'producto_nuevo': row[44].lower() == 'true',
                                              })
                supplierinfo_id = imp_process(supplierinfo_obj,
                                              [('product_tmpl_id','=', product_tmpl_id),
                                               ('name','=',partner_id),
                                               ('lote_id','=',wiz.lote_id.id)],
                                              wiz.update_supplierinfo,
                                              {'delay': 1,
						                       'name': partner_id,
						                       'product_tmpl_id': product_tmpl_id,
                                               'lote_id': wiz.lote_id.id,
						                       'minimum_production': _f(row[36]),
						                       'stocking_status': row[37],
						                       'stocking_status': 'On Demand',
						                       'supplier_price': _c(row[38]),
						                       'service_fee': _c(row[39]),
						                       'carton_quantity': _c(row[30]),
						                       'carton_weight': _c(row[31]),
						                       'carton_width': _c(row[32]),
						                       'carton_length': _c(row[33]),
						                       'carton_heigth': _c(row[34]),
						                       'carton_volume': _c(row[35]),
						                       'min_qty': _f(row[36]),
                                              })
                if supplierinfo_id:
                    si_ids.append(supplierinfo_id)

        return {
            'name': _('Supplier info'),
            'domain': [('id', 'in', si_ids)],
            'res_model': 'product.supplierinfo',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
        }

catalog_import()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
