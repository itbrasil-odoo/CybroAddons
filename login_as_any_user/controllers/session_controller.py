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
import datetime
import logging

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SessionController(http.Controller):
    """Controller to provide session information to the client"""

    @http.route("/web/session/check_impersonation", type="json", auth="user")
    def check_impersonation(self):
        """Checks if the current session is impersonated and returns information"""
        session = request.session
        result = {"is_impersonated": False}

        if hasattr(session, "is_impersonated") and session.is_impersonated:
            result["is_impersonated"] = True

            if hasattr(session, "impersonated_by"):
                result["impersonated_by"] = session.impersonated_by

            if hasattr(session, "session_timeout"):
                result["session_timeout"] = session.session_timeout

                # Check if session expired
                try:
                    # Convert string to datetime if necessary
                    if isinstance(session.session_timeout, str):
                        timeout = datetime.datetime.fromisoformat(
                            session.session_timeout
                        )
                    else:
                        timeout = session.session_timeout

                    now = fields.Datetime.now()
                    if now > timeout:
                        result["expired"] = True

                        # Atualizar o log de troca
                        if hasattr(session, "switch_log_id"):
                            log = (
                                request.env["login.user.switch.log"]
                                .sudo()
                                .browse(session.switch_log_id)
                            )
                            if log.exists():
                                log.write(
                                    {
                                        "switch_back_date": fields.Datetime.now(),
                                        "note": log.note
                                        + "\n[AUTO] Session expired automatically",
                                    }
                                )
                except Exception as e:
                    _logger.error("Error checking session expiration: %s", str(e))

        return result
