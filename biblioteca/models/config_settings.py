from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Ajustes de Biblioteca guardados en ir.config_parameter
    biblioteca_multa_diaria = fields.Float(
        string="Multa diaria (Biblioteca)",
        config_parameter="biblioteca.multa_diaria",
        default=1.0,
        help="Importe de la multa por día de atraso para préstamos de la biblioteca."
    )

    biblioteca_dias_gracia = fields.Integer(
        string="Días de gracia (Biblioteca)",
        config_parameter="biblioteca.dias_gracia",
        default=0,
        help="Cantidad de días de gracia antes de comenzar a calcular la multa por atraso."
    )
