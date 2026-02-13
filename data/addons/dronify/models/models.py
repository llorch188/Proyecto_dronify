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
            # Generar el codigo del paquete en base a la fecha
            if not vals.get('codigo'):
                vals['codigo'] = datetime.now().strftime('%Y%m%d%H%M%S')
        return super().create(vals_list)
        
# ----------------------------------------------------------------------------------------------------------------------------

# MODELO VUELOS
class vuelos(models.Model):
    _name = 'dronify.vuelos'
    _description = 'Vuelos'

    codigo = fields.Char( # Generado automaticamente formato: YYYYMMDDHHMMSS. Solo lectura
    string="Código",
    readonly=True,
    copy=False
    ) 
    name = fields.Char( # Obligatorio y valor por defecto: YYYYMMDD_Vuelo
        string="Nombre",
        copy=False
    ) 

    # Relacion many 2 one del dron asignado, obligatorio
    dron_id = fields.Many2one(
        'dronify.drones', # Modelo destino de la relacion
        string='Dron asignado', # Etiqueta en la interfaz
        ondelete='set null', # Si elimina el vuelo se queda en null(no borra el dron)
        help='Id del dron que se ha asignado al dron' # Texto de ayuda
    )

    # Relacion many 2 one con el piloto
    piloto_id = fields.Many2one( # Obligatorio solo para los pilotos (Preguntar)
        'dronify.contactos',
        string='Piloto asignado al vuelo.',
        ondelete='set null',
        help='Id del piloto asignado al vuelo.'
    )
    
    # Relacion one 2 many con los id de los paquetes a transportar
    paquete_ids = fields.One2many(
    'dronify.paquetes', 
    'codigo', 
    string='Paquetes del vuelo')

    preparado = fields.Boolean()
    realizado = fields.Boolean()
    peso_total = fields.Float( # Campo computado (Sumad el peso de todos los paquetes)
        string="Peso total",
        compute="_compute_peso_total",
        store=True
    )
    consumo_estimado = fields.Float( # Campo computado (aproximacion de consumo del vuelo)
        consumo_estimado = fields.Float(
        string="Consumo estimado (%)",
        compute="_compute_consumo_estimado",
        store=True
        )
    )

    # Metodos de los botones
    def action_preparar_vuelo(self):
        self.preparado = True

    def action_desbloquear(self):
        self.preparado = False

    def action_finalizar_vuelo(self):
        self.realizado = True
    
    @api.model_create_multi # Campo capacidad_max obligatorio
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                raise UserError("El nombre del vuelo es obligatorio")
            if not vals.get('dron_id'):
                raise UserError("Debe asignar un dron.")
            if not vals.get('piloto_id'):
                raise UserError("Debe asignar un piloto.")
            # Generar el codigo del vuelo en base a la fecha
            if not vals.get('codigo'):
                vals['codigo'] = datetime.now().strftime('%Y%m%d%H%M%S_Vuelo')
        return super().create(vals_list)
        
    # Campo computado del peso total 
    @api.depends('paquete_ids', 'paquete_ids.peso')
    def _compute_peso_total(self):
        for vuelo in self:
            total = 0.0
        for paquete in vuelo.paquete_ids:
            total += paquete.peso or 0.0
        vuelo.peso_total = total

    # Campo computado del consumo estimado
    @api.depends('peso_total', 'dron_id.capacidad_max')
    def _compute_consumo_estimado(self):
        for vuelo in self:
            if vuelo.dron_id and vuelo.dron_id.capacidad_max:
                vuelo.consumo_estimado = (
                vuelo.peso_total / vuelo.dron_id.capacidad_max
            ) * 100
        else:
            vuelo.consumo_estimado = 0