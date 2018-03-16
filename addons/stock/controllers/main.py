# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape

import json


class BarcodeController(http.Controller):

    @http.route(['/stock/barcode/'], type='http', auth='user')
    def a(self, debug=False, **k):
        if not request.session.uid:
            return http.local_redirect('/web/login?redirect=/stock/barcode/')

        return request.render('stock.barcode_index')


class StockReportController(http.Controller):

    @http.route('/stock/<string:output_format>/<string:report_name>/<string:model_name>/<int:report_id>', type='http', auth='user')
    def report(self, output_format, report_name, model_name, token, report_id=False, **kw):
        uid = request.session.uid
        domain = [('create_uid', '=', uid)]
        model_name = model_name.replace('_', '.')
        stock_report = request.env[model_name].sudo(uid).search(domain, limit=1)
        for arg in kw:
            kw[arg] = json.loads(kw[arg])
        try:
            if output_format == 'pdf':
                response = request.make_response(
                    stock_report.with_context(active_id=report_id).get_pdf(**kw),
                    headers=[
                        ('Content-Type', 'application/pdf'),
                        ('Content-Disposition', 'attachment; filename=' + report_name + '.pdf;')
                    ]
                )
                response.set_cookie('fileToken', token)
                return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
