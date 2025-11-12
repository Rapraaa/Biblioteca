# from odoo import http


# class BibliotecaPractica(http.Controller):
#     @http.route('/biblioteca_practica/biblioteca_practica', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/biblioteca_practica/biblioteca_practica/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('biblioteca_practica.listing', {
#             'root': '/biblioteca_practica/biblioteca_practica',
#             'objects': http.request.env['biblioteca_practica.biblioteca_practica'].search([]),
#         })

#     @http.route('/biblioteca_practica/biblioteca_practica/objects/<model("biblioteca_practica.biblioteca_practica"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('biblioteca_practica.object', {
#             'object': obj
#         })

