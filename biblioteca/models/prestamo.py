# -*- coding: utf-8 -*-
from odoo import api, fields, models

class BibliotecaPrestamo(models.Model):
    _name = 'biblioteca.prestamo'
    _description = 'Préstamo de libro'

    name = fields.Char(string='Referencia', required=True, readonly=True, default='Nuevo')
    libro_id = fields.Many2one('biblioteca.libro', string='Libro', required=True, ondelete='restrict')
    socio_id = fields.Many2one('res.partner', string='Socio/Estudiante', required=True, ondelete='restrict')
    fecha_prestamo = fields.Date(string='Fecha préstamo', default=fields.Date.context_today)
    fecha_devolucion = fields.Date(string='Fecha devolución')
    dias_atraso = fields.Integer(string='Días de atraso')

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('biblioteca.prestamo') or 'Nuevo'
        return super().create(vals)

from odoo import models, fields

class BibliotecaPrestamo(models.Model):
    _inherit = "biblioteca.prestamo"
    socio_cedula = fields.Char(string="Cédula", related="socio_id.cedula", store=False)

