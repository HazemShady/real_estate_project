from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class RealEstateMaintenancePortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(RealEstateMaintenancePortal, self)._prepare_portal_layout_values()
        maintenance_count = request.env['maintenance.request'].sudo().search_count([
            ('assigned_to', '=', request.env.user.id)
        ])

        values.update({
            'maintenance_count': maintenance_count,
        })
        return values

    @http.route(['/my/maintenance', '/my/maintenance/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_maintenance_requests(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        maintenance_requests = request.env['maintenance.request'].sudo().search([
            ('assigned_to', '=', request.env.user.id)
        ], order='create_date desc')

        values.update({
            'maintenance_requests': maintenance_requests,
        })
        return request.render('real_estate.portal_my_maintenance_requests', values)
