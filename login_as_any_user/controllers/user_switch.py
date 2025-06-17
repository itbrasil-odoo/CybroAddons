"""controller for switching user """
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
from odoo import fields, http
from odoo.http import request
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)


class UserSwitch(http.Controller):
    """This is a controller to switch user and switch back to admin
    user_switch:
        this function is to check whether the user has permission to switch users
    switch_admin:
        function to switch back to admin
    """

    @http.route("/switch/user", type="json", auth="user")
    def user_switch(self):
        """
        Summary:
            function to check whether current user has permission to switch users
        Return:
            whether the current user is allowed to switch or not
        """
        if not request.env.user.has_group("login_as_any_user.group_login_as_any_user"):
            return False
        return True

    @http.route("/switch/admin", type="json", auth="user")
    def switch_admin(self):
        """
        Summary:
            function to move back to admin
        Return:
            the home page to be loaded
        """
        session = request.session
        if not hasattr(session, "previous_user") or not session.previous_user:
            return False

        # Get the original user to switch back to
        pre_uid = session.previous_user
        pre_user = request.env["res.users"].sudo().browse(pre_uid)

        # Store switch log ID before clearing session
        switch_log_id = (
            session.switch_log_id if hasattr(session, "switch_log_id") else False
        )

        # If user exists, switch back without permission checks
        if pre_user and pre_user.exists():
            # Record the return in the log
            if switch_log_id:
                log = request.env["login.user.switch.log"].sudo().browse(switch_log_id)
                if log.exists():
                    log.write({"switch_back_date": fields.Datetime.now()})

            # Get the login before clearing session
            pre_login = pre_user.login

            # Clear impersonation flags before switching back
            session.is_impersonated = False
            session.impersonated_by = None
            session.switch_log_id = None
            session.session_timeout = None

            # Important: temporarily store previous_user to bypass permission check
            orig_previous_user = session.previous_user
            session.previous_user = None

            # Create a fresh cursor for authentication to avoid permission issues
            # Commit any pending changes before creating a new cursor
            request.env.cr.commit()

            # Use a completely different approach to bypass authentication issues
            try:
                # Get the user's password from the database directly
                cr = Registry(request.env.cr.dbname).cursor()
                try:
                    # Get the original admin user's password hash
                    cr.execute("SELECT password FROM res_users WHERE id=%s", (pre_uid,))
                    res = cr.fetchone()
                    password_hash = res[0] if res else False

                    if password_hash:
                        # Directly set the user ID in the session
                        request.session.uid = pre_uid
                        request.session.login = pre_login

                        # Update environment with new user
                        request.env = odoo.api.Environment(
                            request.env.cr, pre_uid, request.env.context
                        )

                        # Force redirect to home page
                        return {
                            "type": "ir.actions.act_url",
                            "url": "/?nocache=" + str(fields.Datetime.now()),
                            "target": "self",
                        }
                    else:
                        _logger.error(
                            "Could not find password hash for user %s", pre_uid
                        )
                        return False
                finally:
                    cr.close()
            except Exception as e:
                # Restore previous_user if authentication fails
                session.previous_user = orig_previous_user
                _logger.error("Error switching back to original user: %s", str(e))
                return False
        return False
