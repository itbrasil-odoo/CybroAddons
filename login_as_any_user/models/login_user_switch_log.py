#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################


from odoo import api, fields, models


class LoginUserSwitchLog(models.Model):
    """Model to store user switch logs"""

    _name = "login.user.switch.log"
    _description = "Login User Switch Log"
    _order = "create_date desc"

    admin_user_id = fields.Many2one(
        "res.users",
        string="Admin User",
        readonly=True,
        required=True,
        help="Administrator user who initiated the switch",
    )
    switched_to_user_id = fields.Many2one(
        "res.users",
        string="Switched To User",
        readonly=True,
        required=True,
        help="User to which the switch was made",
    )
    ip_address = fields.Char(
        readonly=True,
        help="IP address from where the switch was made",
    )
    switch_date = fields.Datetime(
        readonly=True,
        default=lambda self: fields.Datetime.now(),
        help="Date and time of the user switch",
    )
    duration = fields.Float(
        readonly=True,
        help="Duration of session in minutes",
        compute="_compute_duration",
        store=True,
    )
    switch_back_date = fields.Datetime(
        readonly=True,
        help="Date and time of the return to the administrator user",
    )
    note = fields.Text()

    @api.depends("switch_back_date")
    def _compute_duration(self):
        """Calcula a duração da sessão em minutos"""
        for record in self:
            if record.switch_back_date:
                delta = record.switch_back_date - record.switch_date
                record.duration = delta.total_seconds() / 60.0
            else:
                # Se ainda não retornou, calcular com o horário atual
                now = fields.Datetime.now()
                delta = now - record.switch_date
                record.duration = delta.total_seconds() / 60.0
