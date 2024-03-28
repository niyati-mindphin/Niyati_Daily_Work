odoo.define('dynco_base.tree_button', function(require) {
    "use strict";
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var TreeButton = ListController.extend({
        buttons_template: 'dynco_base.buttons',
        events: _.extend({}, ListController.prototype.events, {
            'click .open_wizard_action': '_OpenWizard',
        }),
        _OpenWizard: function() {
            var self = this;
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'add.discount',
                name: 'Add Discounts',
                view_mode: 'list',
                view_type: 'list',
                views: [
                    [false, 'form']
                ],
                target: 'new',
                res_id: false,
            });
        }
    });
    var StockQuantListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: TreeButton,
        }),
    });
    viewRegistry.add('button_in_tree', StockQuantListView);
});