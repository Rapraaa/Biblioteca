from odoo import fields, models

class PrestamoMultaRel(models.Model):
    _inherit = 'biblioteca.prestamo'

    # Relación 1:N desde el préstamo hacia las multas
    multa_ids = fields.One2many(
        'biblioteca.multa',   # modelo destino
        'prestamo_id',        # campo Many2one en biblioteca.multa
        string='Multas'
    )
