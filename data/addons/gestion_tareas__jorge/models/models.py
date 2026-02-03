from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

# =================================================
# MODELO: TAREA
# =================================================
class GestionTarea(models.Model):
    _name = 'gestion_tareas__jorge.tarea'
    _description = 'Gestión de tareas'

    name = fields.Char(string="Título de la tarea")

    description = fields.Text(
        string="Descripción",
        required=True
    )

    fecha_inicio = fields.Date(
        string="Fecha inicio",
        required=True
    )

    fecha_fin = fields.Date(
        string="Fecha fin",
        compute="_compute_fecha_fin",
        store=True
    )

    historia_id = fields.Many2one(
        'gestion_tareas__jorge.historia',
        string='Historia de usuario',
        ondelete='set null'
    )

    tecnologia_ids = fields.Many2many(
        'gestion_tareas__jorge.tecnologia',
        'rel_tarea_tecnologia',
        'tarea_id',
        'tecnologia_id',
        string="Tecnologías"
    )

    @api.depends('fecha_inicio')
    def _compute_fecha_fin(self):
        for record in self:
            record.fecha_fin = (
                record.fecha_inicio + timedelta(days=7)
                if record.fecha_inicio else False
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('description'):
                raise UserError("La descripción de la tarea es obligatoria.")
        return super().create(vals_list)

    def write(self, vals):
        if 'description' in vals and not vals.get('description'):
            raise UserError("La descripción no puede quedar vacía.")
        return super().write(vals)


# =================================================
# MODELO: HISTORIA
# =================================================
class GestionHistoria(models.Model):
    _name = 'gestion_tareas__jorge.historia'
    _description = 'Historia de usuario'

    name = fields.Char(required=True)
    description = fields.Text(required=True)

    proyecto_id = fields.Many2one(
        'gestion_tareas__jorge.proyecto',
        ondelete='cascade'
    )

    tarea_ids = fields.One2many(
        'gestion_tareas__jorge.tarea',
        'historia_id'
    )


# =================================================
# MODELO: PROYECTO
# =================================================
class GestionProyecto(models.Model):
    _name = 'gestion_tareas__jorge.proyecto'
    _description = 'Proyecto'

    name = fields.Char(required=True)
    description = fields.Text(required=True)

    historia_ids = fields.One2many(
        'gestion_tareas__jorge.historia',
        'proyecto_id'
    )


# =================================================
# MODELO: TECNOLOGÍA
# =================================================
class GestionTecnologia(models.Model):
    _name = 'gestion_tareas__jorge.tecnologia'
    _description = 'Tecnología'

    name = fields.Char(required=True)

    desarrollador_ids = fields.Many2many(
        'res.partner',
        'rel_dev_tec',
        'tecnologia_id',
        'desarrollador_id',
        string="Desarrolladores"
    )


# =================================================
# HERENCIA: DESARROLLADORES (res.partner)
# =================================================
class ResPartner(models.Model):
    _inherit = 'res.partner'

    tecnologia_ids = fields.Many2many(
        'gestion_tareas__jorge.tecnologia',
        'rel_dev_tec',
        'desarrollador_id',
        'tecnologia_id',
        string="Tecnologías"
    )


# =================================================
# MODELO: SPRINT
# =================================================
class GestionSprint(models.Model):
    _name = 'gestion_tareas__jorge.sprint'
    _description = 'Sprint del proyecto'

    nombre = fields.Char(required=True)
    fecha_ini = fields.Datetime(required=True)
    duracion = fields.Integer()

    fecha_fin = fields.Datetime(
        compute='_compute_fecha_fin',
        store=True
    )

    proyecto_id = fields.Many2one(
        'gestion_tareas__jorge.proyecto',
        ondelete='set null'
    )

    @api.depends('fecha_ini', 'duracion')
    def _compute_fecha_fin(self):
        for record in self:
            record.fecha_fin = (
                record.fecha_ini + timedelta(days=record.duracion)
                if record.fecha_ini and record.duracion else False
            )
