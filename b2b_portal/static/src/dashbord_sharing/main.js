/** @odoo-module **/
import { startWebClient } from '@web/start';
import { DashboardB2BPortalWebClient } from './dashbord_sharing';
import { removeServices } from './removeservice';

removeServices();
startWebClient(DashboardB2BPortalWebClient);
