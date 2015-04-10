# -*- coding: utf-8 -*-
from openerp import api, models


class PlannerCrm(models.Model):

    _inherit = 'web.planner'

    @api.model
    def _get_planner_application(self):
        planner = super(PlannerCrm, self)._get_planner_application()
        planner.append(['planner_crm', 'CRM Planner'])
        return planner

    @api.model
    def _prepare_planner_crm_data(self):
        sales_team = self.env.ref('sales_team.team_sales_department')
        values = {
            'prepare_backend_url': self.prepare_backend_url,
            'alias_domain': sales_team.alias_domain,
            'alias_name': sales_team.alias_name,
        }
        return values
