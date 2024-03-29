odoo.define('b2b_portal.b2b_product_quick_view', function (require) {
'use strict';

require('website_sale_comparison.comparison');
const ajax = require('web.ajax');
const Dialog = require('web.Dialog');
const publicWidget = require('web.public.widget');
const { ProductCarouselMixins } = require('theme_prime.mixins');
const OwlDialog = require('web.OwlDialog');
const QuickViewDialog = require('theme_prime.product_quick_view');

publicWidget.registry.b2b_product_quick_view = publicWidget.Widget.extend({
    selector: '.b2b-product-quick-view-action, .tp_hotspot[data-on-hotspot-click="modal"]',
    read_events: {
        'click': '_onClick',
    },
    /**
     * @private
     * @param  {Event} ev
     */
    _onClick: function (ev) {
        // debugger;
        this.QuickViewDialog = new QuickViewDialog(this, {
            variantID: parseInt($(ev.currentTarget).attr('data-variant-id')),
        }).open();
    },
});

return QuickViewDialog;

});
