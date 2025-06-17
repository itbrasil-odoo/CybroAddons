/** @odoo-module **/
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {Component, useState, onWillStart} from "@odoo/owl";
import {browser} from "@web/core/browser/browser";

export class ImpersonationBanner extends Component {
    setup() {
        this.user = useService("user");
        this.rpc = useService("rpc");
        this.state = useState({
            isImpersonating: false,
            userName: "",
            adminName: "",
            timeRemaining: "",
            sessionTimeout: null,
        });

        onWillStart(async () => {
            await this.checkImpersonation();
            // Set timer to update remaining time every minute
            this.timer = browser.setInterval(() => {
                this.checkImpersonation();
            }, 60000); // 1 minute
        });
    }

    willUnmount() {
        if (this.timer) {
            browser.clearInterval(this.timer);
            this.timer = null;
        }
    }

    async checkImpersonation() {
        // Check if current session is impersonated
        try {
            const session = await this.rpc("/web/session/check_impersonation");
            if (session.is_impersonated) {
                this.state.isImpersonating = true;
                this.state.userName = this.user.name;
                this.state.adminName = session.impersonated_by;
                this.state.sessionTimeout = session.session_timeout;
                this.updateTimeRemaining();

                // Se expirou, redirecionar
                if (session.expired) {
                    await this.onSwitchBack();
                }
            } else {
                this.state.isImpersonating = false;
            }
        } catch (error) {
            console.error("Failed to check impersonation status:", error);
        }
    }

    updateTimeRemaining() {
        if (!this.state.sessionTimeout) return;

        const now = new Date();
        const timeout = new Date(this.state.sessionTimeout);
        const diffMs = timeout - now;

        if (diffMs <= 0) {
            this.state.timeRemaining = "Expirado";
            this.onSwitchBack();
        } else {
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMins / 60);
            const remainingMins = diffMins % 60;

            if (diffHours > 0) {
                this.state.timeRemaining = `${diffHours}h ${remainingMins}m`;
            } else {
                this.state.timeRemaining = `${remainingMins}m`;
            }
        }
    }

    async onSwitchBack() {
        await this.rpc("/switch/admin");
        window.location.reload();
    }
}

ImpersonationBanner.template = "login_as_any_user.ImpersonationBanner";
ImpersonationBanner.props = {};

// Add the component to the top of all web pages
registry.category("main_components").add("impersonation_banner", {
    Component: ImpersonationBanner,
    props: {},
});
