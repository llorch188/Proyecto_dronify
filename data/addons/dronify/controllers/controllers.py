# from odoo import http


# class Dronify(http.Controller):
#     @http.route('/dronify/dronify', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dronify/dronify/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('dronify.listing', {
#             'root': '/dronify/dronify',
#             'objects': http.request.env['dronify.dronify'].search([]),
#         })

#     @http.route('/dronify/dronify/objects/<model("dronify.dronify"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dronify.object', {
#             'object': obj
#         })

