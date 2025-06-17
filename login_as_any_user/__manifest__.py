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
{
    "name": "Login As Any User",
    "version": "16.0.2.0.0",
    "category": "Extra Tools",
    "summary": "Admin can log in as any user - Enhanced Security",
    "author": "Cybrosys Techno Solution, IT Brasil",
    "maintainer": "Cybrosys Techno Solution",
    "company": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["base"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/login_switch_log_views.xml",
        "wizards/user_selection_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "login_as_any_user/static/src/js/systray_button.js",
            "login_as_any_user/static/src/js/impersonation_banner.js",
            "login_as_any_user/static/src/xml/systray_button_templates.xml",
            "login_as_any_user/static/src/xml/impersonation_banner.xml",
        ]
    },
    "images": ["static/description/banner.png"],
    "license": "LGPL-3",
    "installable": True,
    "auto-install": False,
    "application": False,
}
