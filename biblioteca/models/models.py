# -*- coding: utf-8 -*-

import requests
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class BibliotecaAutor(models.Model):
    _name = 'biblioteca.autor'
    _description = 'Autor de la Biblioteca'
    _rec_name = 'display_name'

    firstname = fields.Char(string='Nombre')
    lastname = fields.Char(string='Apellido')
    nacimiento = fields.Date()
    display_name = fields.Char(compute='_compute_display_name', store=True)
    libro_ids = fields.One2many('biblioteca.libro', 'autor', string='Libros Escritos')

    @api.depends('firstname', 'lastname')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.firstname or ''} {record.lastname or ''}".strip()


class BibliotecaEditorial(models.Model):
    _name = 'biblioteca.editorial'
    _description = 'Editorial de libros'

    name = fields.Char(string='Nombre Editorial', required=True)
    pais = fields.Char(string='País')
    ciudad = fields.Char(string='Ciudad')


class BibliotecaLibro(models.Model):
    _name = 'biblioteca.libro'
    _description = 'Libro de la Biblioteca'
    _rec_name = 'titulo'

    firstname = fields.Char(string='Nombre de búsqueda')
    titulo = fields.Char(string='Título del Libro')
    autor = fields.Many2one('biblioteca.autor', string='Autor')
    ejemplares = fields.Integer(string='Número de ejemplares', default=1)
    costo = fields.Float(string='Costo')
    description = fields.Text(string='Resumen del libro')
    fecha_publicacion = fields.Date(string='Fecha de Publicación')
    genero = fields.Char(string='Género')
    isbn = fields.Char(string='ISBN')
    paginas = fields.Integer(string='Páginas')
    editorial = fields.Many2one('biblioteca.editorial', string='Editorial')
    ubicacion = fields.Char(string='Categoría')

    prestamo_ids = fields.One2many('biblioteca.prestamo', 'libro_id', string='Historial de Préstamos')

    multa_bloqueo_id = fields.Many2one('biblioteca.multa',    #define si el libro sirve o si esta bloqueado por algo
                                       string='Multa que Bloquea', 
                                       readonly=True, 
                                       help="Indica si el libro está bloqueado por una multa de tipo Dañado o Perdido.") #esto sirve para documentar
    
    bloqueado = fields.Boolean(compute='_compute_bloqueado', store=True, string='Bloqueado por Multa')

    @api.depends('multa_bloqueo_id') #cada que cambie la multa esto se ejecute
    def _compute_bloqueado(self):
        for record in self:
            record.bloqueado = bool(record.multa_bloqueo_id) #si existe regresa true, sino falsoe

    def action_buscar_openlibrary(self):
        for record in self:
            if not record.firstname:
                raise UserError("Por favor, ingrese un nombre en 'Nombre de búsqueda' antes de buscar en OpenLibrary.")
            try:
                url = f"https://openlibrary.org/search.json?q={record.firstname}&language=spa"
                response = requests.get(url, timeout=8)
                response.raise_for_status()
                data = response.json()
                if not data.get('docs'):
                    raise UserError("No se encontró ningún libro con ese nombre en OpenLibrary.")
                libro = data['docs'][0]
                work_key = libro.get('key')
                titulo = libro.get('title', 'Sin título')
                autor_nombre = libro.get('author_name', ['Desconocido'])[0]
                anio = libro.get('first_publish_year')
                editorial_nombre = libro.get('publisher', ['Desconocido'])[0]
                paginas = 0
                descripcion = ''
                generos = []
                isbn = libro.get('isbn', [None])[0] if libro.get('isbn') else None

                if work_key:
                    work_url = f"https://openlibrary.org{work_key}.json"
                    work_resp = requests.get(work_url, timeout=10)
                    if work_resp.ok:
                        work_data = work_resp.json()
                        if isinstance(work_data.get('description'), dict):
                            descripcion = work_data['description'].get('value', '')
                        elif isinstance(work_data.get('description'), str):
                            descripcion = work_data['description']
                        if work_data.get('subjects'):
                            generos = work_data['subjects'][:3]
                        editions_url = f"https://openlibrary.org{work_key}/editions.json"
                        editions_resp = requests.get(editions_url, timeout=10)
                        if editions_resp.ok:
                            editions_data = editions_resp.json()
                            if editions_data.get('entries'):
                                entry = editions_data['entries'][0]
                                paginas = entry.get('number_of_pages', 0)
                                isbn = entry.get('isbn_10', [None])[0] if entry.get('isbn_10') else isbn
                                editorial_nombre = entry.get('publishers', [None])[0] if entry.get('publishers') else editorial_nombre

                autor = self.env['biblioteca.autor'].search([('firstname', '=', autor_nombre)], limit=1)
                if not autor:
                    autor = self.env['biblioteca.autor'].create({'firstname': autor_nombre})
                editorial = self.env['biblioteca.editorial'].search([('name', '=', editorial_nombre)], limit=1)
                if not editorial:
                    editorial = self.env['biblioteca.editorial'].create({'name': editorial_nombre})

                record.write({
                    'titulo': titulo,
                    'autor': autor.id,
                    'isbn': isbn or 'No disponible',
                    'paginas': paginas or 0,
                    'fecha_publicacion': datetime.strptime(str(anio), '%Y').date() if anio else None,
                    'description': descripcion or 'No hay descripción disponible.',
                    'editorial': editorial.id,
                    'genero': ', '.join(generos) if generos else 'Desconocido',
                })
            except Exception as e:
                raise UserError(f"Error al conectar con OpenLibrary: {str(e)}")


class BibliotecaUsuario(models.Model):
    _name = 'biblioteca.usuario'
    _description = 'Usuario/Lector de la Biblioteca'
    _rec_name = 'name'

    name = fields.Char(string='Nombre Completo', required=True)
    cedula = fields.Char(string='Cédula', size=10)
    email = fields.Char(string='Email')
    phone = fields.Char(string='Teléfono')
    
    prestamo_ids = fields.One2many('biblioteca.prestamo', 'usuario_id', string='Préstamos Realizados')
    multa_ids = fields.One2many('biblioteca.multa', 'usuario_id', string='Multas')

    prestamo_count = fields.Integer(string='Número de Préstamos', compute='_compute_prestamo_count', store=True)
    multa_pendiente_count = fields.Integer(string='Multas Pendientes', compute='_compute_multa_pendiente_count', store=True)
    bloqueado_prestamo = fields.Boolean(compute='_compute_bloqueado_prestamo', store=True, string='Bloqueado para Préstamos')

    @api.depends('prestamo_ids')
    def _compute_prestamo_count(self):
        for record in self:
            record.prestamo_count = len(record.prestamo_ids)

    @api.depends('multa_ids.state')
    def _compute_multa_pendiente_count(self):
        for record in self:
            record.multa_pendiente_count = len(record.multa_ids.filtered(lambda m: m.state == 'pendiente'))

    # NUEVO: Compute para el bloqueo del usuario
    @api.depends('multa_pendiente_count')
    def _compute_bloqueado_prestamo(self):
        for record in self:
            record.bloqueado_prestamo = record.multa_pendiente_count > 0

    @api.constrains('cedula')
    def _check_cedula(self):
        for record in self:
            if record.cedula:
                # Validar que solo sean números
                if not record.cedula.isdigit():
                    raise ValidationError("La cédula debe contener solo números.")
                
                # Validar que tenga exactamente 10 dígitos
                if len(record.cedula) != 10:
                    raise ValidationError("La cédula debe tener exactamente 10 dígitos.")
                
                # Validar provincia (primeros 2 dígitos)
                provincia = int(record.cedula[0:2])
                if provincia < 1 or provincia > 24:
                    raise ValidationError(f"Código de provincia inválido: {provincia}. Debe estar entre 01 y 24.")
                
                # Validar algoritmo de cédula ecuatoriana
                if not self._validar_cedula_ec(record.cedula):
                    raise ValidationError(f"Cédula ecuatoriana inválida: {record.cedula}")

    def _validar_cedula_ec(self, cedula):
        if len(cedula) != 10 or not cedula.isdigit():
            return False
        
        provincia = int(cedula[0:2])
        if provincia < 1 or provincia > 24:
            return False
        
        coef = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        total = 0
        for i in range(9):
            val = int(cedula[i]) * coef[i]
            if val >= 10:
                val -= 9
            total += val
        
        digito_verificador = 10 - (total % 10) if total % 10 != 0 else 0
        return digito_verificador == int(cedula[9])


class BibliotecaPersonal(models.Model):
    _name = 'biblioteca.personal'
    _description = 'Personal de la biblioteca'

    name = fields.Char(string='Nombre Completo', required=True)
    cargo = fields.Char(string='Cargo')
    telefono = fields.Char(string='Teléfono')
    email = fields.Char(string='Email')


class BibliotecaConfiguracion(models.Model):
    _name = 'biblioteca.configuracion'
    _description = 'Configuración de Multas y Notificaciones'

    name = fields.Char(string='Nombre', default='Configuración de Biblioteca', required=True)
    dias_prestamo = fields.Integer(string='Días de Préstamo', default=7, required=True,
                                   help='Número de días permitidos para el préstamo de un libro')
    dias_gracia_notificacion = fields.Integer(string='Días de Gracia para Notificación', default=1, required=True,
                                              help='Días después del vencimiento antes de enviar correo de multa')
    monto_multa_dia = fields.Float(string='Monto de Multa por Día', default=1.0, required=True,
                                   help='Monto en dólares que se cobra por cada día de retraso')
    email_biblioteca = fields.Char(string='Email de la Biblioteca', 
                                   default='biblioteca@ejemplo.com',
                                   help='Email desde el cual se enviarán las notificaciones')

    @api.model
    def get_config(self):
        config = self.search([], limit=1)
        if not config:
            config = self.create({
                'name': 'Configuración de Biblioteca',
                'dias_prestamo': 7,
                'dias_gracia_notificacion': 1,
                'monto_multa_dia': 1.0,
                'email_biblioteca': 'biblioteca@ejemplo.com'
            })
        return config


class BibliotecaPrestamo(models.Model):
    _name = 'biblioteca.prestamo'
    _description = 'Registro de Préstamo de Libro'
    _rec_name = 'name'

    name = fields.Char(string='Prestamo', required=True, copy=False)
    fecha_prestamo = fields.Datetime(default=fields.Datetime.now, string='Fecha de Préstamo')
    libro_id = fields.Many2one('biblioteca.libro', string='Libro', required=True)
    usuario_id = fields.Many2one('biblioteca.usuario', string='Usuario', required=True)
    email_lector = fields.Char(string='Email del Lector', related='usuario_id.email', store=True, readonly=True)
    fecha_devolucion = fields.Datetime(string='Fecha de Devolución')
    multa_bol = fields.Boolean(default=False, string='Tiene Multa')
    multa = fields.Float(string='Monto Multa', readonly=True)
    fecha_maxima = fields.Datetime(compute='_compute_fecha_maxima', store=True, string='Fecha Máxima de Devolución')
    usuario = fields.Many2one('res.users', string='Usuario presta', default=lambda self: self.env.uid)
    dias_retraso = fields.Integer(string='Días de Retraso', compute='_compute_dias_retraso', store=True)
    notificacion_enviada = fields.Boolean(string='Notificación Enviada', default=False)
    fecha_notificacion = fields.Datetime(string='Fecha de Notificación', readonly=True)

    estado = fields.Selection([
        ('b', 'Borrador'),
        ('p', 'Prestado'),
        ('m', 'Con Multa'),
        ('d', 'Devuelto')
    ], string='Estado', default='b')

    @api.constrains('libro_id', 'usuario_id', 'estado')
    def _check_prestamo_disponibilidad(self):
        for rec in self:
            if rec.estado in ['b', 'p']: # Solo se valida en borrador o al prestar
                # Restricción Lector: No puede tener multas pendientes
                if rec.usuario_id.bloqueado_prestamo:
                    raise ValidationError(f"El usuario {rec.usuario_id.name} tiene multas pendientes y está bloqueado para nuevos préstamos.")

                # Restricción Libro: No puede estar Dañado o Perdido
                if rec.libro_id.bloqueado:
                    raise ValidationError(f"El libro '{rec.libro_id.titulo}' está bloqueado porque fue reportado como {rec.libro_id.multa_bloqueo_id.tipo_multa.capitalize()} en el préstamo {rec.libro_id.multa_bloqueo_id.prestamo_id.name}.")

                # Restricción de stock, si aplica
                prestamos_activos = self.search_count([
                    ('libro_id', '=', rec.libro_id.id),
                    ('estado', 'in', ['p', 'm']) # Consideramos prestado/multado como fuera de stock
                ])
                if prestamos_activos >= rec.libro_id.ejemplares:
                    raise ValidationError(f"No hay ejemplares disponibles de '{rec.libro_id.titulo}'.")

    @api.depends('fecha_prestamo')
    def _compute_fecha_maxima(self):
        config = self.env['biblioteca.configuracion'].get_config()
        for record in self:
            if record.fecha_prestamo:
                record.fecha_maxima = record.fecha_prestamo + timedelta(days=config.dias_prestamo)
            else:
                record.fecha_maxima = False

    @api.depends('fecha_maxima', 'fecha_devolucion', 'estado')
    def _compute_dias_retraso(self):
        for record in self:
            if record.estado in ['p', 'm'] and record.fecha_maxima:
                fecha_actual = fields.Datetime.now()
                if fecha_actual > record.fecha_maxima:
                    diferencia = fecha_actual - record.fecha_maxima
                    record.dias_retraso = diferencia.days
                else:
                    record.dias_retraso = 0
            elif record.estado == 'd' and record.fecha_devolucion and record.fecha_maxima:
                if record.fecha_devolucion > record.fecha_maxima:
                    diferencia = record.fecha_devolucion - record.fecha_maxima
                    record.dias_retraso = diferencia.days
                else:
                    record.dias_retraso = 0
            else:
                record.dias_retraso = 0

    @api.model
    @api.model
    def create(self, vals_list):
        # El método create recibe una lista de diccionarios (vals_list)
        # Iteramos sobre la lista
        for vals in vals_list:
            # Aplicamos la secuencia a cada diccionario 'vals' individual
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('biblioteca.prestamo') or '/'
        
        # Llamamos al super() original con la lista de diccionarios modificada
        return super().create(vals_list)

    def generar_prestamo(self):
        for rec in self:
            rec.write({'estado': 'p'})
            return True

    def action_devolver(self):
        """Registra la devolución y genera multa si hay retraso"""
        for rec in self:
            fecha_devolucion = fields.Datetime.now()
            
            if fecha_devolucion > rec.fecha_maxima:
                # CREACIÓN DE MULTA POR RETRASO
                diferencia = fecha_devolucion - rec.fecha_maxima
                dias_retraso = diferencia.days
                config = self.env['biblioteca.configuracion'].get_config()
                monto_multa_dia = config.monto_multa_dia
                monto_total = dias_retraso * monto_multa_dia

                rec._generar_multa_automatica(dias_retraso, monto_multa_dia)
                
                self.env['biblioteca.multa'].create({
                    'usuario_id': rec.usuario_id.id,
                    'prestamo_id': rec.id,
                    'monto': monto_total,
                    'dias_retraso': dias_retraso,
                    'fecha_vencimiento': fecha_devolucion.date() + timedelta(days=30),
                    'state': 'pendiente'
                })
                
                rec.write({
                    'fecha_devolucion': fecha_devolucion,
                    'estado': 'm', # Estado de Multa
                    'multa_bol': True,
                    'multa': monto_total # Usar el monto total recalculado
                })
            else:
                rec.write({
                    'fecha_devolucion': fecha_devolucion,
                    'estado': 'd',
                    'multa_bol': False,
                    'multa': 0.0
                })
    # NUEVO: Botón para reportar Dañado
    def action_reportar_danado(self):
        return self._generar_multa_manual('danado')

    # NUEVO: Botón para reportar Perdido
    def action_reportar_perdido(self):
        return self._generar_multa_manual('perdido')
    
    def _generar_multa_manual(self, tipo):
        """Genera multa manual (Dañado o Perdido)"""
        self.ensure_one()
        config = self.env['biblioteca.configuracion'].get_config()
        
        # Monto para multas Dañado/Perdido: Usaremos el costo del libro o un valor fijo
        monto = self.libro_id.costo or 50.0 # Usar el costo del libro como base
        dias_retraso = 0

        multa = self.env['biblioteca.multa'].create({
            'usuario_id': self.usuario_id.id,
            'prestamo_id': self.id,
            'tipo_multa': tipo, # TIPO: DAÑADO o PERDIDO
            'monto': monto,
            'dias_retraso': dias_retraso,
            'fecha_vencimiento': fields.Date.today() + timedelta(days=60), # Más tiempo para gestión
            'state': 'pendiente'
        })

        # CONSECUENCIA 2: Bloqueo del Libro
        self.libro_id.write({'multa_bloqueo_id': multa.id})

        self.write({
            'fecha_devolucion': fields.Datetime.now(),
            'estado': 'm', # Estado de Multa
            'multa_bol': True,
            'multa': monto
        })
        
        # Opcional: Enviar notificación específica para daño/pérdida
        
        return True # Devuelve True si se ejecuta correctamente
    


    @api.model
    def _cron_verificar_prestamos_vencidos(self):
        _logger.info("=== INICIANDO VERIFICACIÓN DE PRÉSTAMOS VENCIDOS ===")
        
        config = self.env['biblioteca.configuracion'].get_config()
        fecha_actual = fields.Datetime.now()
        
        prestamos_vencidos = self.search([
            ('estado', '=', 'p'),
            ('fecha_maxima', '<', fecha_actual),
            ('notificacion_enviada', '=', False),
        ])
        
        _logger.info(f"Préstamos vencidos encontrados: {len(prestamos_vencidos)}")
        
        for prestamo in prestamos_vencidos:
            dias_retraso = (fecha_actual - prestamo.fecha_maxima).days
            
            if dias_retraso >= config.dias_gracia_notificacion:
                _logger.info(f"Procesando préstamo {prestamo.name} - Retraso: {dias_retraso} días")
                
                multa = prestamo._generar_multa_automatica(dias_retraso, config)
                
                if prestamo.email_lector:
                    prestamo._enviar_correo_multa(multa, config)
                else:
                    _logger.warning(f"Préstamo {prestamo.name} no tiene email")
                
                prestamo.write({
                    'estado': 'm',
                    'multa_bol': True,
                    'notificacion_enviada': True,
                    'fecha_notificacion': fecha_actual
                })
        
        _logger.info("=== VERIFICACIÓN COMPLETADA ===")

    def _generar_multa_automatica(self, dias_retraso, monto_multa_dia):
        """
        Crea o actualiza una multa de tipo 'retraso' para el préstamo actual.
        Recibe el monto por día para asegurar un cálculo preciso al actualizar.
        """
        self.ensure_one()
        
        # 1. Buscar si ya existe una multa *pendiente* de tipo 'retraso' para este préstamo
        multa_existente = self.env['biblioteca.multa'].search([
            ('prestamo_id', '=', self.id),
            ('tipo_multa', '=', 'retraso'), 
            ('state', '=', 'pendiente')
        ], limit=1)
        
        # Recalcular el monto total con los días de retraso más recientes
        monto_actualizado = dias_retraso * monto_multa_dia
        
        if multa_existente:
            # 2. Actualizar multa existente
            multa_existente.write({
                'dias_retraso': dias_retraso,
                'monto': monto_actualizado
            })
            _logger.info(f"Multa por retraso actualizada {multa_existente.name} - Monto: ${monto_actualizado}")
            return multa_existente
        else:
            # 3. Crear nueva multa
            fecha_vencimiento = fields.Date.today() + timedelta(days=30)
            
            multa = self.env['biblioteca.multa'].create({
                'usuario_id': self.usuario_id.id,
                'prestamo_id': self.id,
                'tipo_multa': 'retraso', # CLAVE: Se añade el tipo de multa
                'monto': monto_actualizado,
                'dias_retraso': dias_retraso,
                'fecha_vencimiento': fecha_vencimiento,
                'state': 'pendiente'
            })
            
            # Actualizar el campo 'multa' en el registro de préstamo (se hace en el else/creación)
            self.write({'multa': monto_actualizado})
            _logger.info(f"Nueva multa por retraso creada {multa.name} - Monto: ${monto_actualizado}")
            return multa

    def _enviar_correo_multa(self, multa, config):
        try:
            template = self.env.ref('biblioteca.email_template_notificacion_multa', raise_if_not_found=False)
            
            if not template:
                _logger.error("Plantilla de correo no encontrada")
                return False
            
            template.send_mail(self.id, force_send=True)
            _logger.info(f"Correo enviado a {self.email_lector} para préstamo {self.name}")
            return True
            
        except Exception as e:
            _logger.error(f"Error al enviar correo para préstamo {self.name}: {str(e)}")
            return False


class BibliotecaMulta(models.Model):
    _name = 'biblioteca.multa'
    _description = 'Multa por Retraso de Libro'
    _rec_name = 'name'

    name = fields.Char(string='Referencia de Multa', 
                      default=lambda self: self.env['ir.sequence'].next_by_code('biblioteca.multa'), 
                      readonly=True)
    usuario_id = fields.Many2one('biblioteca.usuario', string='Lector Multado', required=True)
    prestamo_id = fields.Many2one('biblioteca.prestamo', string='Préstamo Origen', required=True, ondelete='restrict')
    tipo_multa = fields.Selection([
        ('retraso', 'Retraso'),
        ('danado', 'Dañado'),
        ('perdido', 'Perdido')
    ], string='Tipo de Multa', required=True, default='retraso', readonly=True) # Por defecto será 'retraso' si es automática
    monto = fields.Float(string='Monto de la Multa', required=True)
    dias_retraso = fields.Integer(string='Días de Retraso', required=True)
    fecha_vencimiento = fields.Date(string='Fecha de Vencimiento', required=True)

    state = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada')
    ], string='Estado', default='pendiente', required=True)

    def action_pagar(self):
        self.ensure_one()
        self.state = 'pagada'
        
       #al pagar se revisa si debemos liberar al libro o al usuario para que no este en perdio
        if self.tipo_multa in ['perdido', 'danado'] and self.prestamo_id.libro_id.multa_bloqueo_id == self: #el and revisa si es esta la multa que causa el vloqueo
            # Liberar el libro pq estaba perdido o dañado
            self.prestamo_id.libro_id.write({'multa_bloqueo_id': False}) 
        
        # se pasa a estado d, osea devuelto
        if self.prestamo_id.fecha_devolucion or self.tipo_multa in ['perdido', 'danado']:
            self.prestamo_id.write({'estado': 'd'})
        
        _logger.info(f"Multa {self.name} marcada como pagada")