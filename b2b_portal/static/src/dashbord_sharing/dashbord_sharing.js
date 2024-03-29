/** @odoo-module **/

import { useBus, useEffect, useService } from '@web/core/utils/hooks';
import { ActionContainer } from '@web/webclient/actions/action_container';
import { MainComponentsContainer } from "@web/core/main_components_container";
import { useOwnDebugContext } from "@web/core/debug/debug_context";
import { ErrorHandler, NotUpdatable } from "@web/core/utils/components";
import { session } from '@web/session';
const { Component } = owl;
// const { useEffect} = owl;

export class DashboardB2BPortalWebClient extends Component {
    setup() {
        window.parent.document.body.style.margin = "0"; // remove the margin in the parent body
        this.actionService = useService('action');
        this.user = useService("user");
        useService("legacy_service_provider");
        useOwnDebugContext({ categories: ["default"] });
        useEffect(
            () => {
                this._showView();
            },
            () => []
        );
    }

    handleComponentError(error, C) {
        // remove the faulty component
        this.Components.splice(this.Components.indexOf(C), 1);
        /**
         * we rethrow the error to notify the user something bad happened.
         * We do it after a tick to make sure owl can properly finish its
         * rendering
         */
        Promise.resolve().then(() => {
            throw error;
        });
    }

    async _showView() {
        debugger;
        const { action_name } = session;
        await this.actionService.doAction(
            action_name,
            {
                props: {
                    preventEdit: false,
                    preventCreate: false,
                },
                additionalContext: {
                    no_breadcrumbs: true,
                }
            }
        );
    }
}

DashboardB2BPortalWebClient.components = { ActionContainer, ErrorHandler, NotUpdatable, MainComponentsContainer };
DashboardB2BPortalWebClient.template = 'b2b_portal.dashbord_sharing';
