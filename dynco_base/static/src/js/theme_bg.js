/** @odoo-module **/
import { url } from "@web/core/utils/urls";
import { session } from "@web/session";
import { WebClientEnterprise } from "@web_enterprise/webclient/webclient";
import { patch } from 'web.utils';

patch(WebClientEnterprise.prototype, 'dynco_base.WebClientEnterprise', {
    _updateClassList(){
        this._super(...arguments);
        this.update_bg_image();
    },
    update_bg_image(){
        if (!this.el) {
                    return;
        }
        if(this.hm.hasHomeMenu){
            if (session.theme_has_background_image) {
                var backgroundImageUrl = url('/web/image', {
                    model: 'res.company',
                    field: 'background_image',
                    id: this.env.services.company.currentCompany.id,
                });
                $(this.el).attr('style', 'background-image:"'+backgroundImageUrl+'!important;"');
            }else{
                $(this.el).attr('style', '');
            }
            
        }else{
            $(this.el).attr('style', '');
        }
    }
});

export default WebClientEnterprise;