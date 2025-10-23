from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BibliotecaUsuario(models.Model):
    _name = 'biblioteca.usuario'
    _description = 'Usuario de Biblioteca'

    name = fields.Char('Nombres y Apellidos', required=True)
    cedula = fields.Char('Cédula (Ecuador)', required=True)
    email = fields.Char('Email')
    phone = fields.Char('Teléfono')
    active = fields.Boolean(default=True)

    @api.onchange('cedula')
    def _onchange_cedula(self):
        if not self.cedula:
            return
        ci = (self.cedula or '').strip()
        if not ci.isdigit() or len(ci) != 10:
            return {
                'warning': {
                    'title': _('Validación'),
                    'message': _('Por favor ingrese bien la cédula (debe tener 10 dígitos numéricos).')
                }
            }
        else:
            return {
                'warning': {
                    'title': _('Validación'),
                    'message': _('La cédula es correcta.')
                }
            }

    @api.constrains('cedula')
    def _check_cedula_len(self):
        for rec in self:
            if not rec.cedula:
                raise ValidationError(_('Por favor ingrese la cédula.'))
            ci = rec.cedula.strip()
            if not ci.isdigit() or len(ci) != 10:
                raise ValidationError(_('Por favor ingrese bien la cédula: 10 dígitos numéricos.'))
