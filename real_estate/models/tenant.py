from passlib import context

from odoo import models, fields, api

class Tenant(models.Model):
    _name = 'real_estate.tenant'
    _description = 'Real Estate Tenant'
    _order = 'name asc'
    
    # === CORE FIELDS ===
    name = fields.Char(string='Tenant Name', required=True, index=True)
    email = fields.Char(string='Email', required=True, index=True)
    phone = fields.Char(string='Phone Number')
    mobile = fields.Char(string='Mobile Number')
    city = fields.Char(string='City')
    date_joined = fields.Date(string='Date Joined', default=fields.Date.today, readonly=True)
    date_of_birth = fields.Date(string='Date of Birth')
    age_category = fields.Selection([
        ('a', '1 to 20'),
        ('b', '21 to 40'),
        ('c', '41 and above'),
    ], string='Age Category')
    
    
    notes = fields.Text(string='Notes')
    active = fields.Boolean(string='Active', default=True) 
    
    
  
    crm_id= fields.Many2one('crm.lead', string='CRM Lead',)
    website_id = fields.Many2one('website', string='Website',)
  

    def update_notes(self,):
        """Update the notes field with a new note"""
        for record in self:
            record.write({'notes': record.name})
            
    def update_CRM_Notes(self,):
        """Update the notes field with a new note"""
        for record in self:
            record.write({'notes': record.crm_id.name})    
            
    def update_Website_Notes(self,):
        """Update the notes field with a new note"""
        for record in self:
            if record.website_id:
             record.write({'notes': record.website_id.name}) 
                