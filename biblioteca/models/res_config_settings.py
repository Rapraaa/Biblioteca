# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    biblioteca_multa_diaria = fields.Monetary(
        string='Multa diaria por defecto',
        config_parameter='biblioteca.multa_diaria',
        currency_field='currency_id'
    )
    biblioteca_dias_gracia = fields.Integer(
        string='Días de gracia',
        config_parameter='biblioteca.dias_gracia',
        default=0
    )
