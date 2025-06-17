"""selection wizard for switching user"""

#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj (<https://www.cybrosys.com>)
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
from datetime import timedelta
from odoo import _, api, fields, models
from odoo.exceptions import AccessError
from odoo.http import request


class UserSelection(models.TransientModel):
    """
    class for a wizard for users selection
    _onchange_user_id:
        function to get corresponding user group
    action_switch:
        function for switching the user
    """

    _name = "user.selection"
    _description = "User Selection for Switching"

    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        help="Select the user here",
        domain=lambda self: [("id", "!=", self.env.user.id), ("login", "!=", "admin")],
    )
    access_ids = fields.Many2many(
        "res.groups",
        string="Groups",
        readonly=True,
        compute="_compute_access_ids",
        help="User groups",
    )
    reason = fields.Text(
        string="Reason for Switch", help="Explain why you need to switch to this user"
    )
    session_timeout = fields.Integer(
        string="Session Timeout (minutes)",
        default=60,
        help="Session will automatically expire after this time",
    )

    @api.depends("user_id")
    def _compute_access_ids(self):
        """
        Summary:
            Compute function to get users access groups
        """
        for record in self:
            if record.user_id:
                record.access_ids = record.user_id.groups_id
            else:
                record.access_ids = [(5, 0, 0)]

    def action_switch(self):
        """
        Summary:
            function for switching the user with enhanced security
        Return:
            Main login page after logged in
        """
        self.ensure_one()

        # Check permission
        if not self.env.user.has_group("login_as_any_user.group_login_as_any_user"):
            raise AccessError(_("You don't have permission to switch users."))

        # Register audit log
        ip_addr = request.httprequest.environ.get("REMOTE_ADDR", "unknown")
        log_vals = {
            "admin_user_id": self.env.user.id,
            "switched_to_user_id": self.user_id.id,
            "ip_address": ip_addr,
            "switch_date": fields.Datetime.now(),
            "note": self.reason or "",
        }
        log_id = self.env["login.user.switch.log"].sudo().create(log_vals)

        session = request.session
        session.update(
            {
                "previous_user": self.env.user.id,
                "switch_log_id": log_id.id,
                "is_impersonated": True,
                "impersonated_by": self.env.user.name,
                "session_timeout": fields.Datetime.now()
                + timedelta(minutes=self.session_timeout),
            }
        )

        session.authenticate_without_password(
            self.env.cr.dbname, self.user_id.login, self.env
        )
        return {"type": "ir.actions.act_url", "url": "/", "target": "self"}
