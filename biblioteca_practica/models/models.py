from odoo import models, fields, api, exceptions

from odoo.exceptions import ValidationError 

from datetime import datetime, timedelta


# class biblioteca_practica(models.Model):
#     _name = 'biblioteca_practica.biblioteca_practica'
#     _description = 'biblioteca_practica.biblioteca_practica'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

class biblioteca_libro(models.Model):
    _name = 'biblioteca.libro'
    _description = 'Libros de la biblioteca'
    _rec_name = 'titulo'

    codigo_libro = fields.Char(string='Código del libro') ###nuevo
    titulo = fields.Char(string="Título del libro", required=True)
    autor = fields.Many2one("biblioteca.autor", 
                            string="Autor libro")   #relacion muchos a uno, es decir, muchos libros para un autor
    ejemplares = fields.Integer(string="Número de ejemplares", default=1)
    costo = fields.Float(store=True, string="Costo")
    descripcion = fields.Text(string="Resumen del libro")
    fecha_publicacion = fields.Date(string="Fecha de publicación")
    genero = fields.Char(string="Género")
    isbn = fields.Char(string="ISBN")
    paginas = fields.Integer(string="Número de páginas")
    editorial = fields.Many2one("biblioteca.editorial", string="Editorial")  #Relacion editorial
    ubicacion = fields.Char(string="Categoría")
    
    prestamo_ids = fields.One2many(
        'biblioteca.prestamo', 
        'libro_id', 
        string='Historial de Préstamos'
    )

    available = fields.Boolean(
        string='Disponible', 
        #compute='_compute_available', 
        store=True,
    )


    
    
    
class biblioteca_autor(models.Model):
    _name = "biblioteca.autor"
    _description = "autores de los libros" 
    
    nombre = fields.Char(string="Nombre")
    apellido = fields.Char(string="Apellido")
    nacimiento = fields.Date(string="Fecha de nacimiento")
    libros = fields.Many2many("biblioteca.libro", 
                              "rel_libro_autor", 
                              "id_autor",
                              "id_libro",
                              string="Libros publicados")

    def name_get(self):   #es como ahcer un rec name pero se puede unir cosas, para unir el nombre y apellido queda mas sexy
        resultado = []    #nameget es un hook, Odoo tiene un motor interno que, cuando necesita obtener el nombre legible de un registro busca y llama directamente a una función que se llame name_get(self) en ese modelo.
        for autor in self:
            # Combina el nombre y el apellido.
            name = f"{autor.nombre} {autor.apellido}" 
            # Añade una tupla (ID del registro, Nombre Completo) a la lista.
            resultado.append((autor.id, name))
        return resultado

class biblioteca_editorial(models.Model):
    _name = "biblioteca.editorial"
    _description = "Editoriales"
    _rec_name = 'nombre'
    
    nombre= fields.Char(string="Nombre de la editorial")
    pais= fields.Char(string="País")
    ciudad= fields.Char(string="Ciudad")
    

class biblioteca_prestamo(models.Model):
    _name = 'biblioteca.prestamo'
    _description = 'presta pa ca sapo'
    _rec_name = 'name'  #es para que cuando se refieran a este en otra base de datos se muestre el name en lugar del biblioteca presamo y diga cuando prestamo es
    
    name = fields.Char(required=True, string='Prestamo')
    fecha_prestamo = fields.Datetime(default=datetime.now()) #en caso de no poner fecha se pondra la actual
    libro_id = fields.Many2one('biblioteca.libro') #extrae el id del libro
    usuario_id = fields.Many2one('biblioteca.usuario',string="Usuario")
    fecha_devolucion = fields.Datetime()
    multa_bol = fields.Boolean(default=False)
    multa = fields.Float()
    fecha_maxima = fields.Datetime(compute='_compute_fecha_devolucion')

    usuario = fields.Many2one('res.users', string='Usuario presta',
                              default = lambda self: self.evm.uid) ##explicar
    
    estado = fields.Selection([('b','Borrador'),
                               ('p','Prestamo'),
                               ('m','Multa'),
                               ('d','Devuelto')],
                              string='Estado', default='b')
    
    multas_ids = fields.One2many('biblioteca.multa',
                                 'prestamo',
                                 string='Multas')


class biblioteca_multa(models.Model):
    _name = 'biblioteca.multa'
    _description='multas multosas'

    name = fields.Char(string='código multa')
    
#res name? res partner
#modulo transitorio?
#seprararr en htmls y archivos diferentes
class biblioteca_usuario(models.Model):
    _name = 'biblioteca.usuario'
    _description = 'Usuarios/Clientes de la Biblioteca'
    _rec_name = 'nombre_completo' # Usaremos un campo combinado para el nombre

    nombre = fields.Char(string="Nombre")
    apellido = fields.Char(string="Apellido")
    nombre_completo = fields.Char(string="Nombre Completo", compute='_compute_nombre_completo', store=True)
    cedula = fields.Char('Cédula', required=True)
    email = fields.Char('Email')
    phone = fields.Char('Teléfono')
    active = fields.Boolean(default=True)
    
    # Campo calculado para combinar Nombre y Apellido (similar al name_get, pero para un campo almacenado, como es el usuario se tiene que guardar pues mi so
    @api.depends('nombre', 'apellido')
    def _compute_nombre_completo(self):
        for record in self:
            record.nombre_completo = f"{record.nombre or ''} {record.apellido or ''}".strip() #guarda el nombre completo completito


    # MÉTODO DE VALIDACIÓN
    @api.constrains('cedula') #diferencia api constrain y depends? onchange?
    def _check_cedula(self):
        for record in self:
            cedula = record.cedula
            
            # 1. Verifica la longitud: Debe tener 10 dígitos
            if len(cedula) != 10 or not cedula.isdigit():
                raise exceptions.ValidationError("La Cédula debe contener 10 dígitos numéricos.")

            # 2. Verifica los códigos de provincia (los dos primeros dígitos)
            provincia = int(cedula[0:2])
            if provincia < 1 or provincia > 24:
                 raise exceptions.ValidationError("Los dos primeros dígitos de la Cédula no corresponden a una provincia válida (1-24).")
            
            # 3. Lógica del dígito verificador (la parte más importante y compleja)
            tercer_digito = int(cedula[2]) #vuelve entero al 3 digito de la cedula
            if tercer_digito < 0 or tercer_digito > 6: 
                raise exceptions.ValidationError("El tercer dígito de la Cédula no es válido (debe ser 0-6 para persona natural).")
                
            # 4. Cálculo final del dígito verificador (Algoritmo Módulo 10)
            coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
            sumatoria = 0
            
            for i in range(9):
                digito = int(cedula[i]) * coeficientes[i]
                sumatoria += digito if digito < 10 else (digito - 9)

            digito_final = (sumatoria % 10)
            digito_final = 0 if digito_final == 0 else (10 - digito_final)

            # 5. Compara el dígito calculado con el dígito real
            if digito_final != int(cedula[9]):
                raise exceptions.ValidationError(f"El número de Cédula '{cedula}' es inválido.")