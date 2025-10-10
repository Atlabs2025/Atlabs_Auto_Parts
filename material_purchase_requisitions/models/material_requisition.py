from odoo import models, api

class MaterialPurchaseRequisition(models.Model):
    _inherit = 'material.purchase.requisition'

    # @api.model
    # def default_get(self, fields_list):
    #     res = super().default_get(fields_list)
    #     # if context contains uid, use it to find employee
    #     uid = self.env.uid
    #     employee = self.env['hr.employee'].search([('user_id', '=', uid)], limit=1)
    #     if employee:
    #         res['employee_id'] = employee.id
    #     return res

    # employee_id = fields.Many2one('hr.employee', string='Employee')
    # job_card_id = fields.Many2one('job.card.management', string='Job Card')
    # job_number = fields.Char(string='Job Number')
    # from_job_card_origin = fields.Boolean(string='From Job Card Origin')

    @api.model
    def default_get(self, fields_list):
        """Automatically set logged-in employee when form opens"""
        res = super().default_get(fields_list)
        uid = self.env.uid
        employee = self.env['hr.employee'].search([('user_id', '=', uid)], limit=1)
        if employee:
            res['employee_id'] = employee.id
        return res