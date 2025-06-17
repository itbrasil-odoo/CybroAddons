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
from odoo import fields, http
from odoo.http import request


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

        pre_user = request.env["res.users"].browse(session.previous_user)
        # Check if the user has permission to switch back
        if pre_user:
            # Find the current session log and record the return
            if hasattr(session, "switch_log_id"):
                log = (
                    request.env["login.user.switch.log"]
                    .sudo()
                    .browse(session.switch_log_id)
                )
                if log.exists():
                    log.write({"switch_back_date": fields.Datetime.now()})

            session.authenticate_without_password(
                request.env.cr.dbname, pre_user.login, request.env
            )
            return {"type": "ir.actions.act_url", "url": "/", "target": "self"}
        return False
