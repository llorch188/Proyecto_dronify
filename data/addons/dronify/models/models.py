from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime


# MODELO CONTACTOS
class contactos(models.Model):
    _name = 'dronify.contactos'
    _description = 'Contactos'

    es_cliente = fields.Boolean()
    es_vip = fields.Boolean() # Activa el modo ahorro en vuelos
    es_piloto = fields.Boolean()
    licencia = fields.Char() # Obligatorio si es_piloto == True
    # Relacion many 2 many con los drones
    dron_autorizado_ids = fields.Many2many(
        comodel_name='dronify.drones', # Modelo con el que se relaciona
        relation='relacion_pilotos_drones', # Nombr de la tabla intermediaria en la bddd
        column1='rel_drones', # Nombre de la columna intermediaria referenciando al modelo actual
        column2='rel_contactos', # Nombre de la columna que referencia al otro modelo
        string='Contactos' # Etiqueta en la interfaz
    )
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('es_piloto'):
                if not vals.get('licencia'):
                    raise UserError("La licencia es obligatoria si el usuario es piloto.")
        return super().create(vals_list)

# ----------------------------------------------------------------------------------------------------------------------------

# MODELO DRONES
class drones(models.Model):
    _name = 'dronify.drones'
    _description = 'Drones'

    name = fields.Char()
    capacidad_max = fields.Float() # Obligatorio
    bateria = fields.Integer(
        string="Bateria",
        default=100,
        help="Bateria de los drones (100 por defecto)"
    ) 
    estado = fields.Selection(
        [('disponible','Disponible'), ('vuelo','Vuelo'),('taller','Taller')],
        default='disponible'
    )
    # Relacion many 2 many con los drones
    piloto_autorizado_ids = fields.Many2many(
        comodel_name='dronify.contactos',
        relation='relacion_pilotos_drones',
        column1='rel_contactos',
        column2='rel_drones',
        string='Drones'
    )
    @api.model_create_multi # Campo capacidad_max obligatorio
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('capacidad_max'):
                raise UserError("La capacidad máxima del dron es obligatoria.")
        return super().create(vals_list)

# ----------------------------------------------------------------------------------------------------------------------------

# MODELO PAQUETES
class paquetes(models.Model):
    _name = 'dronify.paquetes'
    _description = 'Paquetes'

    codigo = fields.Char( # Generado automaticamente formato: YYYYMMDDHHMMSS. Solo lectura
    string="Código",
    readonly=True,
    copy=False
    ) 
    name = fields.Char() # Obligatorio
    peso = fields.Float() # Obligatorio

    # Relacion many 2 one con el cliente
    cliente_id = fields.Many2one(
        'dronify.contactos', # Modelo destino de la relacion
        string='Cliente del paquete', # Etiqueta en la interfaz
        ondelete='set null', # Si se elimina el paquete el campo se queda null(no elimina el cliente)
        help='Id del cliente al que pertenece el paquete' # Texto de ayuda
    )

    # Relacion many 2 one con el vuelo
    vuelo_id = fields.Many2one(
        'dronify.vuelos',
        string='Vuelo asignado al paquete.',
        ondelete='set null',
        help='Id del vuelo en el cual se ha asignado el paquete.'
    )
    dron_relacionado = fields.Char() # Nombre del dron del vuelo (related solo lectura)

    @api.model_create_multi # Campo capacidad_max obligatorio
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                raise UserError("El nombre del paquete es obligatorio")
            if not vals.get('peso'):
                raise UserError("El peso del paquete es obligatorio")
        return super().create(vals_list)
    
    # Generar el codigo del paquete en base a la fecha
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('codigo'):
                vals['codigo'] = datetime.now().strftime('%Y%m%d%H%M%S')
        return super().create(vals_list)
    
# ----------------------------------------------------------------------------------------------------------------------------

# MODELO VUELOS
