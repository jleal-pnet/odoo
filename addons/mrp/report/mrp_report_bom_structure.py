# -*- coding: utf-8 -*-

from odoo import api, models

class ReportBomStructure(models.AbstractModel):
    _name = 'report.mrp.report_bom_structure'

    @api.model
    def get_report_values(self, docids, data=None):
        docs = []
        for bom_id in docids:
            doc = self.env['mrp.bom.report']._get_pdf_line(bom_id, unfolded=True)
            doc['report_type'] = 'pdf'
            doc['report_structure'] = 'all'
            docs.append(doc)
        return {
            'doc_ids': docids,
            'doc_model': 'mrp.bom',
            'docs': docs,
        }
