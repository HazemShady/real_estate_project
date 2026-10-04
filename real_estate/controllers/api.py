import odoo
from odoo import http, fields
from odoo.http import request
import json
import secrets
from functools import wraps

class RealEstateAPI(http.Controller):
    """Integration routes; public/none routes using sudo bypass normal model ACLs."""
    
    @http.route('/api/properties/create', type='json', auth='public', methods=['POST'], csrf=False)
    def create_property(self, **kwargs):
        """Create a property from supplied integration fields using elevated access."""
        try:
            params = kwargs
            print(request.env.user.name)
            # if not request.env.user.has_group('real_estate.group_property_manager'):
            #     return {
            #         'status': 'error',
            #         'message': 'You do not have permission to create properties'
            #     }
            # Validate required fields
            if not params.get('name') or not params.get('price'):
                return {
                    'status': 'error',
                    'message': 'Name and price are required'
                }
            
            # Create property
            property_obj = request.env['real_estate.property'].sudo().create({
                'name': params.get('name'),
                'price': params.get('price'),
                'bedrooms': params.get('bedrooms', 0),
                'property_type': params.get('property_type', 'house'),
                'external_id': params.get('external_id'),
            })
            
            return {
                'status': 'success',
                'message': 'Property created successfully',
                'data': {
                    'property_id': property_obj.id,
                    'name': property_obj.name,
                    'external_id': property_obj.external_id
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
     #******************************************************       
          
    @http.route('/api/tenant/create', type='json', auth='public', methods=['POST'], csrf=False)
    def create_tenant(self, **kwargs):
        """Create a tenant from the supported integration fields."""
        try:
            params = kwargs
            if not params.get('name') or not params.get('email'):
                return {
                    'status': 'error',
                    'message': 'Name and email are required'
                }
            
            tenant = request.env['real_estate.tenant'].sudo().create({
                'name': params.get('name'),
                'email': params.get('email'),
                'notes': params.get('Notes'),
                'phone': params.get('phone'),
                'mobile': params.get('mobile'),
                'city': params.get('city'),
                'created_by_api': True,
                'date_of_birth': params.get('date_of_birth'),
                'notes': params.get('notes'),
                # 'website': params.get('website'),
                'age_category': params.get('age_category'),
            })
            
            return {
                'status': 'success',
                'message': 'Tenant created successfully',
                'data': {
                    'tenant_id': tenant.id,
                    'name': tenant.name,
                    'email': tenant.email,
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
   #******************************************************       

    @http.route('/api/tenant/update_phone', type='json', auth='public', methods=['PUT'], csrf=False)
    def update_tenant_phone(self, **kwargs):
        """Update only the phone field on an active tenant selected by ID."""
        tenant_id = kwargs.get('tenant_id')
        phone = kwargs.get('phone')
        if not tenant_id or phone is None:
            return {
                'status': 'error',
                'message': 'tenant_id and phone are required',
            }

        try:
            tenant_id = int(tenant_id)
        except (TypeError, ValueError):
            return {
                'status': 'error',
                'message': 'tenant_id must be an integer',
            }

        tenant = request.env['real_estate.tenant'].sudo().browse(tenant_id).exists()
        if not tenant:
            return {
                'status': 'error',
                'message': 'Tenant not found',
            }

        if not tenant.active:
            return {
                'status': 'error',
                'message': 'Cannot update phone for an inactive tenant',
            }

        tenant.write({'phone': phone})
        return {
            'status': 'success',
            'message': 'Tenant phone updated successfully',
            'data': {
                'tenant_id': tenant.id,
                'phone': tenant.phone,
            },
        }

    
     #******************************************************       
        
    @http.route('/api/lead/create', type='json', auth='public', methods=['POST'], csrf=False)
    def create_lead(self, **kwargs):
        """Create a CRM lead with the real-estate fields supplied by the caller."""
        try:
            params = kwargs
            if not params.get('name') or not params.get('email') or not params.get('phone') or not params.get('property_type') :
                return {
                    'status': 'error',
                    'message': 'Name and email are required'
                }
            
            lead = request.env['crm.lead'].sudo().create({
                'name': params.get('name'),
                'email': params.get('email'),
                'phone': params.get('phone'),
                'property_type':params.get('property_type'),
               
            })
            
            return {
                'status': 'success',
                'message': 'lead created successfully',
                'data': {
                    'lead_id': lead.id,
                    'name': lead.name,
                    'email': lead.email,
                    'phone' : lead.phone,
                    'property_type':lead.property_type,
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
   #******************************************************       
          
    @http.route('/api/tenants/<int:tenant_id>', type='http', auth='public', methods=['POST'], csrf=False)
    def update_tenant(self, tenant_id):
        """Update a tenant from the request JSON; the payload currently passes to sudo().write()."""
        tenant_obj = request.env['real_estate.tenant'].sudo().browse(tenant_id)
        # print(tenant_obj.name)
        if not tenant_obj.exists():
            return request.make_json_response(
                {'status': 'error', 
                 'message': 'Tenant not found'}, 
                 status=404
                 )
        
        # This accepts arbitrary writable fields, so this public endpoint needs external authorization.
        params = request.httprequest.get_json(silent=True)

        tenant_obj.write(params)
        return request.make_json_response({'status': 'success', 
                                           'tenant_id': tenant_obj.id}
                                           )        
        
   #******************************************************       

    @http.route('/api/properties/<int:property_id>', type='http', auth='public', methods=['POST'], csrf=False)
    def update_property(self, property_id):
        """Update a property from JSON; the allowlist/authentication boundary is not enforced here."""
        property_obj = request.env['real_estate.property'].sudo().browse(property_id).exists()
        if not property_obj:
            return request.make_json_response(
                {'status': 'error', 'message': 'Property not found'},
                status=404,
            )

        params = request.httprequest.get_json(silent=True)
        if not isinstance(params, dict):
            return request.make_json_response(
                {'status': 'error', 'message': 'A JSON object is required'},
                status=400,
            )

        # The full JSON object is passed through to sudo().write(); restrict it before public deployment.
        property_obj.write(params)
        return request.make_json_response({
            'status': 'success',
            'property_id': property_obj.id,
        })
 #**************************************************************************************************8    
    # @http.route('/api/list_leases', type='http', auth='public', methods=['GET'], csrf=False)
    # def list_leases(self):
    #     tenant_id = request.httprequest.args.get('tenant_id')
    #     if not tenant_id:
    #         return request.make_json_response(
    #             {'status': 'error', 'message': 'tenant_id is required'},
    #              status=400
    #         )

    #     try:
    #         tenant_id = int(tenant_id)
    #     except (TypeError, ValueError):
    #         return request.make_json_response(
    #             {'status': 'error', 'message': 'tenant_id must be an integer'},
    #             status=400,
    #         )

    #     tenant = request.env['real_estate.tenant'].sudo().browse(tenant_id).exists()
    #     if not tenant:
    #         return request.make_json_response(
    #             {'status': 'error', 'message': 'Tenant not found'},
    #             status=404,
    #         )

    #     leases = request.env['real_estate.lease'].sudo().search([
    #         ('tenant_id', '=', tenant_id),
    #     ])
    #     return request.make_response(
    #         json.dumps({
    #             'status': 'success',
    #             'count': len(leases),
    #             'data': [{
    #                 'id': lease.id,
    #                 'name': lease.name,
    #                 'tenant': lease.tenant_id.name,
    #                 'property': lease.property_id.name,
    #                 'start_date': fields.Date.to_string(lease.start_date),
    #                 'end_date': fields.Date.to_string(lease.end_date),
    #                 'monthly_rent': lease.monthly_rent,
    #                 'state': lease.state,
    #             } for lease in leases],
    #         }),
    #         headers={'Content-Type': 'application/json'}
    #     )
#***********************************************************************************************************
    @http.route('/api/list_leases', type='http', auth='none', methods=['GET'], csrf=False)
    def tenant_leases(self, tenant_id):
        """Return lease details for one tenant after checking the legacy bearer token."""
        TOKEN = 'cacb064fd72c08b4459597685'
        authorization_token = request.httprequest.headers.get('Authorization', '')
        if authorization_token != f'Bearer {TOKEN}':
            return request.make_json_response({'status': 'error', 'message': 'Unauthorized'}, status=401)
        if not tenant_id:
            return request.make_json_response(
                {'status': 'error', 
                 'message': 'tenant_id is required'}, 
                 status=400
            )

        try:
            tenant_id = int(tenant_id)
        except (TypeError, ValueError):
            return request.make_json_response(
                {'status': 'error', 'message': 'tenant_id must be an integer'},
                status=400,
            )
       
        leases = request.env['real_estate.lease'].sudo().search([
            ('tenant_id', '=', tenant_id),
        ])
        leases_count = len(leases)
        return request.make_response(
            json.dumps({
                'status': 'success',
                'count': leases_count,
                'data': [{
                    'id': lease.id,
                    'name': lease.name,
                    'start_date': fields.Date.to_string(lease.start_date),
                    'end_date': fields.Date.to_string(lease.end_date),
                    'state': lease.state,
                } for lease in leases],
            }),
            headers={'Content-Type': 'application/json'}
        )
#****************************************************************************
    @http.route(
        '/api/create_lease',
        type='json',
        auth='none',
        methods=['POST'],
        csrf=False,
    )
    # Create a lease for existing tenant/property IDs after the route token check.
    def create_lease(self, **kwargs):
      TOKEN = 'YOUR_TOKEN_HERE'

      authorization_token = request.httprequest.headers.get('Authorization', '')
      if authorization_token != f'Bearer {TOKEN}':
        return {'status': 'error', 'message': 'Unauthorized'}

      try:
        params = kwargs

        required_fields = [
            'tenant_id',
            'property_id',
            'start_date',
            'end_date',
            'monthly_rent',
        ]
        missing_fields = [
            key for key in required_fields if not params.get(key)
        ]
        if missing_fields:
          return {
              'status': 'error',
              'message': 'Required fields are missing',
              'missing_fields': missing_fields,
          }

        tenant_id = int(params['tenant_id'])
        property_id = int(params['property_id'])
        start_date = fields.Date.to_date(params['start_date'])
        end_date = fields.Date.to_date(params['end_date'])
        monthly_rent = float(params['monthly_rent'])

        if not start_date or not end_date:
          raise ValueError('Dates must use YYYY-MM-DD format')
        if start_date > end_date:
          return {
              'status': 'error',
              'message': 'start_date must be on or before end_date',
          }
        if monthly_rent < 0:
          raise ValueError('monthly_rent cannot be negative')

        tenant = (
            request.env['real_estate.tenant'].sudo().browse(tenant_id).exists()
        )
        if not tenant:
          return {'status': 'error', 'message': 'Tenant not found'}

        property_record = (
            request.env['real_estate.property']
            .sudo()
            .browse(property_id)
            .exists()
        )
        if not property_record:
          return {'status': 'error', 'message': 'Property not found'}

        lease = (
            request.env['real_estate.lease']
            .sudo()
            .create({
                'tenant_id': tenant_id,
                'property_id': property_id,
                'start_date': start_date,
                'end_date': end_date,
                'monthly_rent': monthly_rent,
            })
        )

        return {
            'status': 'success',
            'message': 'Lease created successfully',
            'data': {
                'id': lease.id,
                'name': lease.name,
                'tenant_id': lease.tenant_id.id,
                'property_id': lease.property_id.id,
                'start_date': fields.Date.to_string(lease.start_date),
                'end_date': fields.Date.to_string(lease.end_date),
                'monthly_rent': lease.monthly_rent,
                'state': lease.state,
            },
        }

      except (TypeError, ValueError) as e:
        return {'status': 'error', 'message': str(e)}
      except Exception as e:
        return {'status': 'error', 'message': str(e)}
#******************************************************************************
    @http.route('/api/lease/create', type='json', auth='none', methods=['POST'], csrf=False)
    def create_lease(self, **kwargs):
        """Create a tenant and lease together; this route currently references an undefined TOKEN."""
        authorization_token = request.httprequest.headers.get('Authorization', '')
        if authorization_token != f'Bearer {TOKEN}':
            return request.make_json_response({'status': 'error', 'message': 'Unauthorized'}, status=401)
        try:
            params = kwargs
            print(request.env.user.name)
            # Validate required fields
            if not params.get('property_id') or not params.get('start_date') or not params.get('name') or not params.get('email'):
                return {
                    'status': 'error',
                    'message': 'Name and email for Tenant are required'
                }

            tenant_obj = request.env['real_estate.tenant'].sudo().create({
                            'name': params.get('name'),
                            'email': params.get('email'),
                            'phone': "43534",
                            'created_by_api': True,  # Mark the tenant as created via API
                            'external_id': "fdfd90943",
                        })
            if tenant_obj:
                # Create lease
                lease_obj = request.env['real_estate.lease'].sudo().create({
                    'property_id': params.get('property_id'),
                    'tenant_id': tenant_obj.id,
                    'start_date': params.get('start_date'),
                    'end_date': params.get('end_date'),
                })
                
                return {
                    'status': 'success',
                    'message': 'Tenant created successfully',
                    'data': {
                        'name of lease': lease_obj.name,
                        'name of tenant': tenant_obj.name,
                        'email of tenant': tenant_obj.email,

                    }
                }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }