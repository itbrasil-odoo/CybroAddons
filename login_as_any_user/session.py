"""Enhanced secure login as any user without password authentication"""
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
import logging

import odoo
from odoo import _
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)


def authenticate_without_password(self, dbname, login, env):
    """
    Enhanced function for passwordless login with security controls
    and appropriate permission checks
    """
    # Check if the current user has permission to switch users
    current_uid = self.uid

    # If there's no current uid (initial session) check in previous_user
    if not current_uid and hasattr(self, "previous_user"):
        current_uid = self.previous_user

    # If not an admin or a switch back to original user
    if current_uid:
        current_user = env["res.users"].browse(current_uid)
        target_user = env["res.users"].search([("login", "=", login)])

        # If not the user returning to their previous state, check permissions
        if not (
            hasattr(self, "previous_user") and self.previous_user == target_user.id
        ):
            if not current_user.has_group("login_as_any_user.group_login_as_any_user"):
                _logger.warning(
                    "Unauthorized user switch attempt: %s -> %s",
                    current_user.login,
                    login,
                )
                raise AccessError(_("You do not have permission to switch users."))

    registry = Registry(dbname)
    pre_uid = env["res.users"].search([("login", "=", login)]).id
    self.uid = None
    self.pre_login = login
    self.pre_uid = pre_uid

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, pre_uid, {})
        # If 2FA is disabled, we finish immediately
        user = env["res.users"].browse(pre_uid)
        if not user._mfa_url():
            self.finalize(env)

        # Record session information for the impersonation banner
        if hasattr(self, "previous_user"):
            admin_user = env["res.users"].browse(self.previous_user)
            self.is_impersonated = True
            self.impersonated_by = admin_user.name

    if request and request.session is self and request.db == dbname:
        # Like update_env(user=request.session.uid) but works when uid is None
        request.env = odoo.api.Environment(request.env.cr, self.uid, self.context)
        request.update_context(**self.context)

    _logger.info(
        "User %s logged in as %s",
        env["res.users"].browse(current_uid).login if current_uid else "Unknown",
        login,
    )

    return pre_uid
