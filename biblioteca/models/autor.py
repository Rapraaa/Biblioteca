# -*- coding: utf-8 -*-
import logging
import requests
from urllib.parse import quote
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class BibliotecaAutor(models.Model):
    _name = 'biblioteca.autor'
    _description = 'Autor'

    name = fields.Char(string='Nombre', required=True)
    openlib_key = fields.Char(string='OpenLibrary Key', readonly=True)
    birth_date = fields.Char(string='Nacimiento')
    death_date = fields.Char(string='Fallecimiento')
    bio = fields.Text(string='Biografía')
    openlib_last_sync = fields.Datetime(string='Última sincronización', readonly=True)

    def _biografia(self, bio):
        if isinstance(bio, dict):
            return bio.get('value') or ''
        return bio or ''

    def _buscar_openlibrary(self, author_name):
        url = f"https://openlibrary.org/search/authors.json?q={quote(author_name)}"
        _logger.debug("OpenLibrary search URL: %s", url)
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json() or {}
        docs = data.get('docs') or []
        if not docs:
            return None

        lower = author_name.strip().lower()
        best = next((d for d in docs if (d.get('name') or '').strip().lower() == lower), docs[0])
        return best

    def _detalles_autor(self, key):
        if not key:
            return {}
        if not key.startswith('/'):
            key = '/' + key
        url = f"https://openlibrary.org{key}.json"
        _logger.debug("OpenLibrary detail URL: %s", url)
        r = requests.get(url, timeout=10)
        if not r.ok:
            return {}
        return r.json() or {}

    def boton_openlib(self):
        for rec in self:
            if not rec.name:
                raise UserError("Indique el nombre del autor.")
            try:
                doc = rec._buscar_openlibrary(rec.name)
                if not doc:
                    raise UserError("No se encontró el autor en OpenLibrary.")
                key = doc.get('key')
                detail = rec._detalles_autor(key)

                vals = {
                    'openlib_key': key or False,
                    'birth_date': doc.get('birth_date') or detail.get('birth_date') or '',
                    'death_date': doc.get('death_date') or detail.get('death_date') or '',
                    'bio': rec._biografia(detail.get('bio')),
                    'openlib_last_sync': fields.Datetime.now(),
                }
                _logger.info("OpenLibrary: datos aplicados a autor %s -> %s", rec.id, vals)
                rec.write(vals)

            except requests.exceptions.RequestException as e:
                _logger.exception("Error de red consultando OpenLibrary")
                raise UserError(f"Error de red consultando OpenLibrary: {e}")
            except Exception as e:
                _logger.exception("Error genérico consultando OpenLibrary")
                raise UserError(f"Ocurrió un error consultando OpenLibrary: {e}")
