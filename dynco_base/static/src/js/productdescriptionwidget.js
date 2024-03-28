odoo.define('dynco_base.productdescriptionwidget', function (require) {
"use strict";
var core = require('web.core');
var Widget = require('web.Widget');
var {GeneratePriceList} = require('product.generate_pricelist');
var wysiwygLoader = require('web_editor.loader');
    GeneratePriceList.include({
        custom_events: _.extend({}, GeneratePriceList.prototype.custom_events, {
            updated_elemtnotes: 'updatedelemtnotes',
        }),
        init: function (parent, params) {
            this._super(parent, params);
            this.context.quantities = [1];
        },
        start: function () {
            var self = this;
            var def = this._super();
            def.then(function(data){
                if(self.$('.o_content').find('.o_product_description_pricelistwidget').length){
                        self.updatedelemtnotes(self.$('.o_content').find('.o_product_description_pricelistwidget'));
                }
            });
            const $content = this.controlPanelProps.cp_content;
            $content["$searchview"][0].querySelector('.o_is_visible_description').addEventListener('click', this._onClickVisibleDescription.bind(this));
            $content["$searchview"][0].querySelector('.o_is_visible_warehouse').addEventListener('click', this._onClickVisibleWarehouse.bind(this));

            return def;
        },
        updatedelemtnotes:async function(elements){
            if (!elements.length){
                var elements = $('.o_content').find('.o_product_description_pricelistwidget')
            }
            for(var i=0; i < elements.length;i++){
                await this.apply_summer_note(elements[i]);
            }
        },
        apply_summer_note: async function(element){
            var res_id = 1
            if ($(element).attr('pricelist') != undefined){
                res_id = parseInt($(element).attr('pricelist'))
            }
            var wfieldname = element.getAttribute('name');
            var options = {
                    toolbarTemplate: 'web_editor.toolbar',
                    resizable: true,
                    value: $(element).val(),
                    userGeneratedContent: true,
                    recordInfo: {
                        context: this.context,
                        res_model: 'product.pricelist',
                        res_id: res_id,
                        fieldname: wfieldname
                    },
                };
                // this.context.active_id
            var wysiwg = await wysiwygLoader.loadFromTextarea(this, element, options);
            wysiwg.odooEditor.document.addEventListener("focusout", this.focusoutquery.bind(wysiwg));
            
        },
        _onFieldChanged: function (event) {
            var self = this;
            this._super(...arguments);
            self.trigger_up('updated_elemtnotes', {
                elements: $('.o_content').find('.o_product_description_pricelistwidget'),
            });
        },
        focusoutquery: async function(ev, wysiwg){
            var writname = this.options.recordInfo.fieldname;
            var disc = {}
            var self = this;
            disc[writname] = this.getValue();
            await this._rpc({
                model:'product.pricelist',
                method:'write',
                args:[[this.options.recordInfo.res_id], disc]
            });
            self.trigger_up('updated_elemtnotes', {
                elements: $('.o_content').find('.o_product_description_pricelistwidget'),
            });
        },

        _prepareActionReportParams: function () {
            var self = this;
            var def = this._super(...arguments);
            def['is_visible_description'] = this.context.is_visible_description || '';
            def['is_visible_warehouse'] = this.context.is_visible_warehouse || '';
            return def;
        },
        _onClickVisibleDescription(ev) {
            this.context.is_visible_description = ev.currentTarget.checked;
            this._reload();
        },
        _onClickVisibleWarehouse(ev) {
            this.context.is_visible_warehouse = ev.currentTarget.checked;
            this._reload();
        },
    });
});