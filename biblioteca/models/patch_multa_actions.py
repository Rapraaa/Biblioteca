from odoo import api, fields, models

class BibliotecaMulta(models.Model):
    _inherit = 'biblioteca.multa'

    def action_marcar_pagado(self):
        """Marcar la multa como pagada desde el botón de la vista."""
        for rec in self:
            rec.pagado = True
        return True
