from odoo import api, fields, models

class BibliotecaMulta(models.Model):
    _inherit = 'biblioteca.multa'

    # Campos de cálculo/soporte
    dias_atraso = fields.Integer(string='Días de atraso')
    multa_diaria = fields.Float(string='Multa diaria', default=0.0)

    # Campos mostrados en vistas
    monto_multa = fields.Float(string='Monto de la multa', compute='_compute_montos', store=True)
    monto_total = fields.Float(string='Monto total', compute='_compute_montos', store=True)
    pagado = fields.Boolean(string='Pagado', default=False)

    @api.depends('dias_atraso', 'multa_diaria')
    def _compute_montos(self):
        for rec in self:
            base = (rec.dias_atraso or 0) * (rec.multa_diaria or 0.0)
            rec.monto_multa = base
            rec.monto_total = base  # Ajusta si tu lógica real es distinta
