# -*- coding: utf-8 -*-
import requests
from odoo import api, fields, models

class BibliotecaLibro(models.Model):
    _name = 'biblioteca.libro'
    _description = 'Libro'

    name = fields.Char(string='Título', required=True)
    autor_id = fields.Many2one('biblioteca.autor', string='Autor', ondelete='set null')
    anio_pub = fields.Char(string='Año de publicación')
    estado = fields.Selection(
        [('disponible', 'Disponible'), ('prestado', 'Prestado')],
        string='Estado', default='disponible'
    )
    # OpenLib
    isbn = fields.Char(string='ISBN')
    openlib_key = fields.Char(string='OpenLibrary Key', readonly=True)
    number_of_pages = fields.Integer(string='Páginas')

    def _obtener_nombre_autor(self, auth_key):
        try:
            r = requests.get(f'https://openlibrary.org{auth_key}.json', timeout=10)
            r.raise_for_status()
            return r.json().get('name')
        except Exception:
            return None

    def buscar_openlib(self):
        for rec in self:
            if not rec.isbn:
                continue
            try:
                r = requests.get(f'https://openlibrary.org/isbn/{rec.isbn}.json', timeout=10)
                r.raise_for_status()
                b = r.json()
                vals = {
                    'name': b.get('title') or rec.name,
                    'openlib_key': b.get('key'),
                    'number_of_pages': b.get('number_of_pages') or 0,
                }

                publish_date = b.get('publish_date')
                if publish_date:
                    vals['anio_pub'] = publish_date[-4:] if len(publish_date) >= 4 else publish_date

                auths = b.get('authors') or []
                if auths:
                    auth_key = auths[0].get('key')
                    if auth_key:
                        nombre = rec._obtener_nombre_autor(auth_key)
                        if nombre:
                            autor = rec.env['biblioteca.autor'].search([('name', '=', nombre)], limit=1)
                            if not autor:
                                autor = rec.env['biblioteca.autor'].create({'name': nombre, 'openlib_key': auth_key})
                            vals['autor_id'] = autor.id

                rec.write(vals)
            except Exception as e:
                rec.message_post(body=f"OpenLibrary (libro) error: {e}")
