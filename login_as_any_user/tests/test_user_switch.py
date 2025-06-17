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

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestUserSwitch(TransactionCase):
    """Test cases for login_as_any_user module"""

    def setUp(self):
        super().setUp()
        self.admin_user = self.env.ref("base.user_admin")
        # Adicionar o administrador ao grupo de permissão
        self.env.ref("login_as_any_user.group_login_as_any_user").users = [
            (4, self.admin_user.id)
        ]

        # Criar um usuário normal para teste
        self.normal_user = self.env["res.users"].create(
            {
                "name": "Normal User",
                "login": "normal_user",
                "password": "normal_user",
                "groups_id": [(4, self.env.ref("base.group_user").id)],
            }
        )

    def test_01_user_access_rights(self):
        """Testar acesso ao modelo user.selection"""
        # Usuário admin deve ter acesso ao modelo
        self.env.user = self.admin_user
        self.assertTrue(
            self.env["user.selection"].check_access_rights(
                "read", raise_exception=False
            )
        )

        # Usuário normal não deve ter permissão para criar wizard
        # Mas primeiro devemos garantir que ele tenha acesso ao modelo
        # para que o teste não falhe por motivo errado
        self.env.user = self.normal_user
        self.env["user.selection"].check_access_rights("read", raise_exception=True)

        # O teste real é que ele não deveria conseguir realizar a ação
        # de trocar de usuário, que é controlada pelo grupo de segurança
        self.assertFalse(
            self.env.user.has_group("login_as_any_user.group_login_as_any_user"),
            "Usuário normal não deveria ter permissão para trocar de usuário",
        )

    def test_02_log_model_exists(self):
        """Testar se o modelo de log existe e possui os campos esperados"""
        log_model = self.env["login.user.switch.log"]
        # Verificar se os campos básicos existem
        self.assertTrue(hasattr(log_model, "admin_user_id"))
        self.assertTrue(hasattr(log_model, "switched_to_user_id"))
        self.assertTrue(hasattr(log_model, "switch_date"))
        self.assertTrue(hasattr(log_model, "switch_back_date"))
