# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    cedula = fields.Char(string='Cédula', size=10, help='Cédula de 10 dígitos')

    @api.constrains('cedula')
    def _check_cedula_len(self):
        for rec in self:
            if rec.cedula:
                if not rec.cedula.isdigit():
                    raise ValidationError("La cédula debe contener solo números.")
                if len(rec.cedula) != 10:
                    raise ValidationError("Por favor ingrese bien la cédula (debe tener exactamente 10 dígitos).")

    @api.onchange('cedula')
    def _onchange_cedula_warning(self):
        # Aviso no bloqueante al escribir en el formulario
        if self.cedula:
            if (not self.cedula.isdigit()) or (len(self.cedula) != 10):
                return {
                    'warning': {
                        'title': 'Cédula inválida',
                        'message': 'Por favor ingrese bien la cédula (exactamente 10 dígitos numéricos).'
                    }
                }
            # Si es correcta, mostramos un aviso de éxito
            self.env.user.notify_success('La cédula es correcta.')
