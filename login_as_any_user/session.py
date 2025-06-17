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


def _check_switch_permission(env, current_uid, target_uid, session=None):
    """Check if the current user has permission to switch to target user."""
    # Skip permission check if returning to previous user
    if (
        session
        and hasattr(session, "previous_user")
        and session.previous_user == target_uid
    ):
        _logger.info("Allowing switch back to original user: %s", target_uid)
        return True

    # Skip permission check if we're using request and returning to previous user
    if (
        request
        and hasattr(request.session, "previous_user")
        and request.session.previous_user == target_uid
    ):
        _logger.info(
            "Allowing switch back to original user via request session: %s", target_uid
        )
        return True

    # Check if this is a return to original user with bypass flag
    if request and request.session.get("bypass_switch_check"):
        _logger.info("Bypassing permission check due to bypass_switch_check flag")
        return True

    # Regular permission check for normal user switching
    current_user = env["res.users"].browse(current_uid)
    if not current_user.has_group("login_as_any_user.group_login_as_any_user"):
        current_user_login = current_user.login if current_user.exists() else "Unknown"
        _logger.warning(
            "Unauthorized user switch attempt: %s -> %s",
            current_user_login,
            env["res.users"].browse(target_uid).login,
        )
        raise AccessError(_("You do not have permission to switch users."))
    return True


def _setup_impersonation_info(session, env, previous_user_id):
    """Setup impersonation information in the session."""
    try:
        admin_user = env["res.users"].browse(previous_user_id)
        if admin_user.exists():
            session.is_impersonated = True
            session.impersonated_by = admin_user.name
        else:
            session.is_impersonated = True
            session.impersonated_by = "Unknown Admin"
    except Exception as e:
        _logger.warning("Failed to set impersonation info: %s", str(e))
        session.is_impersonated = True
        session.impersonated_by = "System Admin"


def _get_safe_user_name(dbname, user_id):
    """Safely get username for logging purposes."""
    if not user_id:
        return "Unknown"

    try:
        registry = Registry(dbname)
        with registry.cursor() as cr:
            with odoo.api.Environment.manage():
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                user = env["res.users"].browse(user_id)
                return user.login if user.exists() else "Unknown"
    except Exception as e:
        _logger.warning("Failed to get user info: %s", str(e))
        return "Unknown"


def authenticate_without_password(self, dbname, login, env):
    """Enhanced function for passwordless login with security controls."""
    # Identify current user
    current_uid = self.uid if self.uid else getattr(self, "previous_user", False)

    # Find target user ID
    registry = Registry(dbname)
    with registry.cursor() as check_cr:
        with odoo.api.Environment.manage():
            check_env = odoo.api.Environment(check_cr, odoo.SUPERUSER_ID, {})
            target_user = check_env["res.users"].search([("login", "=", login)])
            target_uid = target_user.id if target_user else False

            if not target_uid:
                _logger.error("Target user with login '%s' not found", login)
                raise AccessError(_("User not found."))

            # Check permission if there's a current user
            if current_uid:
                _check_switch_permission(check_env, current_uid, target_uid, self)

    # Prepare session for authentication
    self.uid = None
    self.pre_login = login
    self.pre_uid = target_uid

    # Complete authentication
    with registry.cursor() as cr:
        try:
            new_env = odoo.api.Environment(cr, target_uid, {})
            # Check for 2FA
            user = new_env["res.users"].browse(target_uid)
            if not user._mfa_url():
                # Complete the authentication process
                self.uid = target_uid

            # Setup impersonation info if needed
            if hasattr(self, "previous_user"):
                _setup_impersonation_info(self, new_env, self.previous_user)
        except Exception as e:
            _logger.error("Error during authentication process: %s", str(e))
            raise

    # Update request environment if needed
    if request and request.session is self and request.db == dbname:
        request.env = odoo.api.Environment(request.env.cr, self.uid, self.context)
        request.update_context(**self.context)

    # Log the user switch
    current_user_name = _get_safe_user_name(dbname, current_uid)
    _logger.info("User %s logged in as %s", current_user_name, login)

    return target_uid


# Patch odoo.http.Session with authenticate_without_password
odoo.http.Session.authenticate_without_password = authenticate_without_password
