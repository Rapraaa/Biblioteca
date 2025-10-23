# -*- coding: utf-8 -*-
{
    "name": "Biblioteca",
    "version": "1.0",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",

        "views/actions.xml",                # <-- primero las acciones
        "views/libro_views.xml",
        "views/autor_views.xml",
        "views/usuario_views.xml",
        "views/prestamo_multa_views.xml",
        "views/views.xml"                   # <-- menús al final
    ],
}
