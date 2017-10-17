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

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class sale_order_line_create_multi_lines(models.TransientModel):

    _name = "sale.order.line.create.multi.lines"
    _description = "Sale OrderLine Create Multi"


    @api.multi
    def create_multi_lines(self):
        context = self._context

        model = context.get('active_model', False)
        n = 0
        if model and model == 'sale.order':
            order_ids = context.get('active_ids', [])

            for so in self.env['sale.order'].browse(order_ids):
                olines = so.order_line.filtered(lambda x: not x.adv_issue)

                if not olines: continue

                n += 1
                self.create_multi_from_order_lines(orderlines=olines)

            if n == 0:
                raise UserError(_('There are no Sales Order Lines without Advertising Issues in the selected Sales Orders.'))


        elif model and model == 'sale.order.line':
            orders = []
            line_ids = context.get('active_ids', [])
            for line in self.pool['sale.order.line'].browse(cr, uid, line_ids, context):
                if line.order_id.id not in orders:
                    orders.append(line.order_id.id)

            for oid in orders:
                lines = self.pool['sale.order.line'].search(cr, uid, [('order_id','=', oid),('id','in', line_ids),
                                                                      ('adv_issue','=', False)], context=context)
                if not lines:
                    continue
                n += 1
                olines = self.pool['sale.order.line'].browse(cr, uid, lines, context=context)
                self.create_multi_from_order_lines(cr, uid, olines, context)
            if n == 0:
                raise UserError(_('There are no Sales Order Lines without Advertising Issues in the selection.'))
        return

    @api.model
    def create_multi_from_order_lines(self, orderlines=[]):

        sol_obj = self.env['sale.order.line']

        for ol in orderlines:
            lines = [x.id for x in ol.order_id.order_line]
            number_ids = len([x.id for x in ol.adv_issue_ids])
            if number_ids < 1:
                raise UserError(_('The product Quantity is different from the number of Issues in the multi line.'))

            uom_qty = ol.product_uom_qty / number_ids

            for ad_iss in ol.adv_issue_ids:
                res = {'adv_issue': ad_iss.id, 'adv_issue_ids': False, 'product_uom_qty': uom_qty,
                       'order_id': ol.order_id.id or False,
                       }
                vals = ol.copy_data(default=res)[0]
                mol_rec = sol_obj.create(vals)

                try: del context['__copy_data_seen']
                except: pass
                lines.append(mol_rec.id)

            self._cr.execute("delete from sale_order_line where id = %s"%(ol.id))

        return



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: