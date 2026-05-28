from odoo import models, fields, api
from .logica_dronify import calcular_consumo_vuelo
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


# MODELO CLIENTE
class clientes(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    es_cliente = fields.Boolean()
    es_vip = fields.Boolean() # Activa el modo ahorro en vuelos

# MODELO PILOTO
class pilotos(models.Model):
    _inherit = 'res.partner'

    es_piloto = fields.Boolean()
    licencia = fields.Char() # Obligatorio si es_piloto == True
    # Relacion many 2 many con los drones
    dron_autorizado_ids = fields.Many2many(
        comodel_name='dronify.drones', # Modelo con el que se relaciona
        relation='relacion_pilotos_drones', # Nombr de la tabla intermediaria en la bddd
        column1='rel_drones', # Nombre de la columna intermediaria referenciando al modelo actual
        column2='rel_contactos', # Nombre de la columna que referencia al otro modelo
        string='Drones' # Etiqueta en la interfaz
    )
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('es_piloto') and not vals.get('licencia'):
                raise UserError("La licencia es obligatoria si el usuario es piloto.")
        return super().create(vals_list)
    
    # Comprobacion incluso si se esta editando un piloto ya creado ._.
    @api.constrains('es_piloto', 'licencia')
    def _check_licencia(self):
        for rec in self:
            if rec.es_piloto and not rec.licencia:
                raise ValidationError("La licencia es obligatoria si el usuario es piloto.")

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
        comodel_name='res.partner',
        relation='relacion_pilotos_drones',
        column1='rel_contactos',
        column2='rel_drones',
        string='Pilotos',
        domain=[('es_piloto', '=', True)]  # Mostrar solo pilotos
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
        'res.partner', # Modelo destino de la relacion
        string='Cliente del paquete', # Etiqueta en la interfaz
        ondelete='set null', # Si se elimina el paquete el campo se queda null(no elimina el cliente)
        domain=[('es_cliente', '=', True)], # Mostrar solo los que sean clientes
        help='Id del cliente al que pertenece el paquete' # Texto de ayuda
    )

    # Relacion many 2 one con el vuelo
    vuelo_id = fields.Many2one(
        'dronify.vuelos',
        string='Vuelo asignado al paquete.',
        ondelete='set null',
        help='Id del vuelo en el cual se ha asignado el paquete.'
    )

    # Nombre del dron del vuelo (related solo lectura)
    dron_relacionado = fields.Char(  
        related='vuelo_id.dron_id.name', # Indicar de donde viene este campo(en este caso viene del nombre del dron) 
        string='Dron',
        readonly=True
    )

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

# MODELO ZONAS
class zonas(models.Model):
    _name = 'dronify.zonas'
    _description = 'Zonas'

    name = fields.Char() # Obligatorio
    distancia_km = fields.Float()
    nivel_riesgo = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')],
        string="Nivel de riesgo",
        default='1'
    )
    tarifa_base = fields.Float()
  
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                raise UserError(
                    "El nombre de la zona es obligatorio."
                )
            if not vals.get('nivel_riesgo'):
                raise UserError(
                    "El nivel de riesgo es obligatorio."
                )
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

    distancia_total = fields.Float(
        string="Distancia total (km)",
        default=0.0
    )
    nivel_riesgo = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')],
        string="Nivel de riesgo",
        default='1'
    )

    def _es_vip_cliente(self):
        return any(paquete.cliente_id.es_vip for paquete in self.paquete_ids if paquete.cliente_id)

    # Relacion many 2 one del dron asignado, obligatorio
    dron_id = fields.Many2one(
        'dronify.drones', # Modelo destino de la relacion
        string='Dron asignado', # Etiqueta en la interfaz
        ondelete='set null', # Si elimina el vuelo se queda en null(no borra el dron)
        help='Id del dron que se ha asignado al dron', # Texto de ayuda
    )

    # Relacion many 2 one con el piloto
    piloto_id = fields.Many2one( # Obligatorio solo para los pilotos (Preguntar)
        'res.partner',
        string='Piloto asignado al vuelo.',
        ondelete='set null',
        domain=[('es_piloto', '=', True)],
        help='Id del piloto asignado al vuelo.',
    )
    # Relacion many 2 one con la zona
    zona_id = fields.Many2one(
        'dronify.zonas',
        string='Zona',
        ondelete='set null',
        help='Id de la zona asignada al vuelo.',
    )
    
    # Relacion one 2 many con los id de los paquetes a transportar
    paquete_ids = fields.One2many(
    'dronify.paquetes', 
    'vuelo_id',
    string='Paquetes del vuelo')

    preparado = fields.Boolean()
    realizado = fields.Boolean()
    peso_total = fields.Float( # Campo computado (Sumad el peso de todos los paquetes)
        string="Peso total",
        compute="_compute_peso_total",
        store=True
    )
    consumo_estimado = fields.Float( # Campo computado (aproximacion de consumo del vuelo)
        string="Consumo estimado (%)",
        compute="_compute_consumo_estimado",
        store=True
    )

    consumo_texto = fields.Char(
        string='Consumo estimado',
        compute='_compute_consumo_texto'
    )

    @api.depends('consumo_estimado')
    def _compute_consumo_texto(self):
        for vuelo in self:
            vuelo.consumo_texto = (
                f"{vuelo.consumo_estimado}%"
                if vuelo.consumo_estimado
                else "0%"
            )

    # Metodos de los botones
    def action_preparar_vuelo(self):
        for vuelo in self:
            if not vuelo.zona_id:
                raise UserError("El vuelo debe tener una zona asignada.")
            if not vuelo.paquete_ids:
                raise UserError("El vuelo debe tener al menos un paquete asignado.")
            if not vuelo.dron_id:
                raise UserError("Debe asignar un dron antes de preparar el vuelo.")
            if not vuelo.piloto_id:
                raise UserError("Debe asignar un piloto antes de preparar el vuelo.")
            if vuelo.dron_id.estado != 'disponible':
                raise UserError("El dron debe estar en estado Disponible para preparar el vuelo.")
            if vuelo.peso_total > vuelo.dron_id.capacidad_max:
                raise UserError("El peso total excede la capacidad máxima del dron.")
            if vuelo.consumo_estimado > vuelo.dron_id.bateria:
                raise UserError("No hay batería suficiente para el vuelo estimado.")
            if vuelo.piloto_id not in vuelo.dron_id.piloto_autorizado_ids:
                raise UserError("El piloto seleccionado no está autorizado para este dron.")

            vuelo.preparado = True
            vuelo.dron_id.estado = 'vuelo'

    def action_desbloquear(self):
        for vuelo in self:
            if vuelo.realizado:
                raise UserError(
                    "No se puede desbloquear un vuelo ya finalizado."
                )

            vuelo.preparado = False

            if vuelo.dron_id:
                vuelo.dron_id.estado = 'disponible'

    def action_finalizar_vuelo(self):
        for vuelo in self:
            if not vuelo.preparado:
                raise UserError("Solo se puede finalizar un vuelo que esté preparado.")
            if not vuelo.dron_id:
                raise UserError("El vuelo no tiene dron asignado.")
            vuelo.realizado = True
            vuelo.dron_id.bateria = max(0, vuelo.dron_id.bateria - int(vuelo.consumo_estimado))
            vuelo.dron_id.estado = 'disponible'
    
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

    @api.depends('peso_total','zona_id','paquete_ids','paquete_ids.cliente_id','paquete_ids.cliente_id.es_vip'
    )
    def _compute_consumo_estimado(self):

        for vuelo in self:

            # Si no hay zona no calculamos
            if not vuelo.zona_id:
                vuelo.consumo_estimado = 0.0
                continue

            # Verificar si hay algún cliente VIP
            es_vip = any(
                paquete.cliente_id.es_vip
                for paquete in vuelo.paquete_ids
                if paquete.cliente_id
            )

            # Calcular consumo usando zona
            vuelo.consumo_estimado = (
                calcular_consumo_vuelo(
                    vuelo.peso_total,
                    vuelo.zona_id.distancia_km,
                    int(vuelo.zona_id.nivel_riesgo),
                    es_vip
                )
            )