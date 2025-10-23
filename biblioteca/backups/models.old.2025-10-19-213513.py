from odoo import models, fields

class BibliotecaAutor(models.Model):
    _name = 'biblioteca.autor'
    _description = 'Autor'

    name = fields.Char(string='Nombres', required=True)
    apellidos = fields.Char(string='Apellidos')
    # Relación N:N con libros usando la tabla rel que ya creó el módulo
    libro_ids = fields.Many2many(
        'biblioteca.libro',
        'biblioteca_libros_autor_rel',
        'author_id', 'libro_id',
        string='Libros (N:N)'
    )
