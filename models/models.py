#-*- coding: utf-8 -*-

from odoo import models, fields, api


class biblioteca_libro(models.Model):
    _name = 'biblioteca.libro'
    _description = 'biblioteca.biblioteca' 
    
    firstname = fields.Char(string="Nombre Libro")
    autor = fields.Many2one('biblioteca.autor', string='Autor Libro')
    value = fields.Integer(string='Numero ejemplares')
    publication_date = fields.Integer(string="Año de publicación")
    value2 = fields.Float(compute="_value_pc", store=True, string='Costo') #---- Se guarda en la base de datos 
    isbn = fields.Integer(string="isbn")
    n_paginas = fields.Integer(string="Num Paginas")
    description = fields.Text(string='Resumen Libro')
    genero = fields.Text(string="Género/Categoría")
    estado = fields.Selection([
        ('disponible', 'Disponible'),
        ('reservado', 'Reservado'),
        ('prestado', 'Prestado')
    ], string="Estado", default='disponible')

    @api.depends('value')
    def _value_pc(self):
        for record in self:
            record.value2 = float(record.value) / 100

class BibliotecaAutor(models.Model):
    _name = 'biblioteca.autor'
    _description = 'biblioteca.autor'
    
    #autor_id = fields.integer(string="autor_id") algo no sireve
    firstname = fields.Char()
    lastname = fields.Char()
    
    @api.depends('firstname','lastname')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.firstname} {record.lastname}"
    
class BibliotecaEditorial(models.Model):
    _name = 'biblioteca.editorial'
    _description = 'biblioteca.editorial'
    
    firstname = fields.Char(string="Nombre editorial")
   