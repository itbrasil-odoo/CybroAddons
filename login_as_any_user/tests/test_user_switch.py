#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com\>\)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com\>\)
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
#    If not, see <http://www.gnu.org/licenses/\>.
#
#############################################################################

import unittest.mock as mock

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestUserSwitch(TransactionCase):
    """Test cases for login_as_any_user module"""

    def setUp(self):
        super().setUp()
        self.admin_user = self.env.ref("base.user_admin")
        # Add admin user to the permission group
        self.env.ref("login_as_any_user.group_login_as_any_user").users = [
            (4, self.admin_user.id)
        ]

        # Create a normal test user
        self.normal_user = self.env["res.users"].create(
            {
                "name": "Normal User",
                "login": "normal_user",
                "password": "normal_user",
                "email": "normal_user@example.com",
                "groups_id": [(4, self.env.ref("base.group_user").id)],
            }
        )

    def test_01_user_access_rights(self):
        """Test access to the user.selection model"""
        # Admin user should have access to the model
        self.env.user = self.admin_user
        self.assertTrue(
            self.env["user.selection"].check_access_rights(
                "read", raise_exception=False
            )
        )

        # Normal user should have read access to the model but not switch permission
        self.env.user = self.normal_user
        self.env["user.selection"].check_access_rights("read", raise_exception=True)

        # The real test is that they shouldn't be able to perform the switch action
        # which is controlled by the security group
        self.assertFalse(
            self.env.user.has_group("login_as_any_user.group_login_as_any_user"),
            "Normal user should not have permission to switch users",
        )

    def test_02_log_model_exists(self):
        """Test if the log model exists and has the expected fields"""
        log_model = self.env["login.user.switch.log"]
        # Check if the basic fields exist
        self.assertTrue(hasattr(log_model, "admin_user_id"))
        self.assertTrue(hasattr(log_model, "switched_to_user_id"))
        self.assertTrue(hasattr(log_model, "switch_date"))
        self.assertTrue(hasattr(log_model, "switch_back_date"))
        self.assertTrue(hasattr(log_model, "ip_address"))
        self.assertTrue(hasattr(log_model, "note"))

    def test_03_wizard_creation(self):
        """Test wizard creation and fields"""
        # Only admin should be able to create the wizard
        self.env.user = self.admin_user

        # Create wizard
        wizard = self.env["user.selection"].create(
            {
                "user_id": self.normal_user.id,
                "session_timeout": 60,
                "reason": "Testing user switch functionality",
            }
        )

        # Check wizard fields
        self.assertEqual(wizard.user_id.id, self.normal_user.id)
        self.assertEqual(wizard.session_timeout, 60)
        self.assertEqual(wizard.reason, "Testing user switch functionality")

        # Check access groups computation
        wizard._compute_access_ids()
        self.assertTrue(wizard.access_ids, "User groups should be computed")

    def test_04_wizard_fields_default(self):
        """Test default values for wizard fields"""
        wizard = self.env["user.selection"].create(
            {"user_id": self.normal_user.id, "reason": "Testing user switch"}
        )

        # Check default session timeout
        self.assertEqual(
            wizard.session_timeout, 60, "Default session timeout should be 60 minutes"
        )

    def test_05_log_creation(self):
        """Test log entry creation"""
        # Create a log entry manually
        log = (
            self.env["login.user.switch.log"]
            .sudo()
            .create(
                {
                    "admin_user_id": self.admin_user.id,
                    "switched_to_user_id": self.normal_user.id,
                    "switch_date": fields.Datetime.now(),
                    "ip_address": "127.0.0.1",
                    "note": "Test log entry",
                }
            )
        )

        # Check log entry was created
        self.assertTrue(log.id, "Log entry should be created")
        self.assertEqual(log.admin_user_id.id, self.admin_user.id)
        self.assertEqual(log.switched_to_user_id.id, self.normal_user.id)
        self.assertEqual(log.note, "Test log entry")

        # Record return action
        log.write({"switch_back_date": fields.Datetime.now()})

        self.assertTrue(log.switch_back_date, "Switch back date should be recorded")

    def test_06_permission_check_functions(self):
        """Test permission check functions"""
        # Import the functions to test
        from ..session import _check_switch_permission, _setup_impersonation_info

        # Test permission check - admin should be able to switch users
        self.env.user = self.admin_user
        # Mock session
        session_mock = mock.MagicMock()

        # Check if admin can switch to another user (should pass)
        result = _check_switch_permission(
            self.env, self.admin_user.id, self.normal_user.id, session_mock
        )
        self.assertTrue(result)

        # Check if normal user can switch (should raise AccessError)
        self.env.user = self.normal_user
        with self.assertRaises(AccessError):
            _check_switch_permission(
                self.env, self.normal_user.id, self.admin_user.id, session_mock
            )

        # Test returning to original user (should pass permission check)
        session_mock.previous_user = self.admin_user.id
        result = _check_switch_permission(
            self.env, self.normal_user.id, self.admin_user.id, session_mock
        )
        self.assertTrue(result)

        # Test setup impersonation info
        session_mock = mock.MagicMock()
        _setup_impersonation_info(session_mock, self.env, self.admin_user.id)
        self.assertTrue(session_mock.is_impersonated)
        self.assertEqual(session_mock.impersonated_by, self.admin_user.name)
