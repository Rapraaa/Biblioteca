# -*- coding: utf-8 -*-
from odoo import models, fields

class BibliotecaMulta(models.Model):
    _name = 'biblioteca.multa'
    _description = 'Multa por retraso'

    name = fields.Char(string='Descripción', default='Multa')
    prestamo_id = fields.Many2one('biblioteca.prestamo', string='Préstamo', ondelete='cascade', required=True)
    monto = fields.Float(string='Monto')
    pagado = fields.Boolean(string='Pagado', default=False)
