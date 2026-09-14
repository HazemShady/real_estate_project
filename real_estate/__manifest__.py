# -*- coding: utf-8 -*-
{
    'name': "Real Estate Managment",

    'summary': """
A complete Real Estate Management module for managing properties, units, owners, and tenants efficiently.
Track property availability, sales, rentals, contracts, and related financial transactions in one place.
Designed to simplify real estate operations and provide clear, organized property management workflows.
""",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','crm'],

    # always loaded
    'data': [
    'security/ir.model.access.csv',
    'views/property_views.xml',
    'views/lease_view.xml',
    'views/tenant.xml',
    'views/menu.xml',
      
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',

    ],
}

