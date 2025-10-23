from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta

class Prestamo(models.Model):
    _name = "biblioteca.prestamo"
    _description = "Préstamo"
    _order = "id desc"

    name = fields.Char(string="Referencia", required=True, default="Nuevo", copy=False)
    socio_id = fields.Many2one("res.partner", string="Socio")
    libro_id = fields.Many2one("biblioteca.libro", string="Libro")

    fecha_prestamo = fields.Date(string="Fecha de préstamo")
    fecha_vencimiento = fields.Date(string="Fecha de vencimiento")
    fecha_devolucion = fields.Date(string="Fecha de devolución")

    estado = fields.Selection(
        [
            ("borrador", "Borrador"),
            ("prestado", "Prestado"),
            ("atrasado", "Atrasado"),
            ("devuelto", "Devuelto"),
            ("cancelado", "Cancelado"),
        ],
        string="Estado",
        default="borrador",
        tracking=True,
        required=True,
    )

    dias_gracia = fields.Integer(string="Días de gracia", default=0)
    dias_atraso = fields.Integer(string="Días de atraso", compute="_compute_atraso", store=True)
    multa_diaria = fields.Float(string="Multa diaria", default=1.0)
    monto_multa = fields.Float(string="Monto de la multa", compute="_compute_multa", store=True)

    @api.depends("fecha_vencimiento", "fecha_devolucion", "estado", "dias_gracia")
    def _compute_atraso(self):
        for rec in self:
            rec.dias_atraso = 0
            fecha_ref = rec.fecha_devolucion or fields.Date.today()
            if rec.fecha_vencimiento:
                delta = (fecha_ref - rec.fecha_vencimiento).days
                if delta > rec.dias_gracia:
                    rec.dias_atraso = delta - rec.dias_gracia
            if rec.estado == "prestado" and rec.dias_atraso > 0 and not rec.fecha_devolucion:
                rec.estado = "atrasado"

    @api.depends("dias_atraso", "multa_diaria")
    def _compute_multa(self):
        for rec in self:
            rec.monto_multa = max(rec.dias_atraso, 0) * max(rec.multa_diaria, 0.0)

    def action_confirmar(self):
        for rec in self:
            if rec.estado != "borrador":
                continue
            hoy = fields.Date.today()
            rec.fecha_prestamo = hoy
            rec.fecha_vencimiento = hoy + relativedelta(days=7)
            rec.estado = "prestado"
            if rec.libro_id and hasattr(rec.libro_id, "disponible"):
                rec.libro_id.disponible = False
        return True

    def action_devolver(self):
        for rec in self:
            if rec.estado not in ("prestado", "atrasado"):
                continue
            rec.fecha_devolucion = fields.Date.today()
            rec._compute_atraso()
            rec.estado = "devuelto"
            if rec.libro_id and hasattr(rec.libro_id, "disponible"):
                rec.libro_id.disponible = True
        return True

    def action_cancelar(self):
        for rec in self:
            if rec.estado in ("borrador", "prestado", "atrasado"):
                rec.estado = "cancelado"
                if rec.libro_id and hasattr(rec.libro_id, "disponible"):
                    rec.libro_id.disponible = True
        return True

    @api.model
    def create(self, vals):
        if vals.get("name", "Nuevo") == "Nuevo":
            seq = self.env["ir.sequence"].next_by_code("biblioteca.prestamo") or "PRST-%05d" % (self.env["biblioteca.prestamo"].search_count([]) + 1)
            vals["name"] = seq
        return super().create(vals)
