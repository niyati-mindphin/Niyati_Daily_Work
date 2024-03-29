/** @odoo-module **/

import { registry } from '@web/core/registry';
import Widget from "@web/legacy/js/core/widget";
import publicWidget from "@web/legacy/js/public/public_widget";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

import VariantMixin from "@website_sale/js/sale_variant_mixin";
import wSaleUtils from "@website_sale/js/website_sale_utils";
import { debounce } from "@web/core/utils/timing";

import { renderToElement } from "@web/core/utils/render";
const cartHandlerMixin = wSaleUtils.cartHandlerMixin;


// import { DateTimePicker } from "@web/core/datetime/datetime_picker";


    publicWidget.registry.websiteB2bShopDashBoard = publicWidget.Widget.extend({
        xmlDependencies: ['/theme_prime/static/src/xml/core/snippet_root_widget.xml'],
        selector: ".b2b_portal_shop, .b2b_cart_lines, .b2b_quick_view_qty_update, .b2b_cart_view_page",
        events: {
            'click .tp-load-more-btn': '_onClickLoadMoreProductsBtn',
            'keyup .b2b_o_wsale_products_searchbar_form input[name="search"]': '_onKeyUpProductSearchInput',
            'click .b2b_o_wsale_products_searchbar_form .oe_search_button': '_onSubmitProductSearch',
            'change .b2b_rs_filter_view input[name="hiderrpcheckbox"]': '_onChangeHideRrpCheckBox',
            'change .b2b_rs_filter_view input[name="hideproductpricecheckbox"]': '_onChangehideproductpricecheckbox',
            'click .scan_b2b_product': 'OnScanB2BProducts',
            'change .product_view_b2b input[name="quantity"]': '_onChangeSetQuantity',
            'change .b2b_moble_view input[name="quantity"]': '_onChangeSetQuantity',
            'change input[name="b2bcart_quantity"]': '_onChangeb2bcartQuantity',
            'change input[name="add_quick_qty"]': '_onChangeb2bquickQuantity',
            'submit .b2b_o_wsale_products_searchbar_form': '_onSubmitSaleSearch',
            'click .product_view_b2b button.btn-number': 'onClickAddCartJSON',
            'click .morelink': '_onClickReadMore',
            'click .card .td-qty button.btn-number': 'onClickAddCartJSON',
            'change .oe_cart input[name="note"]': '_onChangeSetNote',
            'change .s_website_form_date .datetimepicker-input': '_onChangeDelivery_date'

        },
        init: function() {
            this._super.apply(this, arguments);
            this.loadedpage = 1;
            this._rpc = this.bindService("rpc");
        },
        start: function() {
            var defs = [this._super.apply(this, arguments)];
            this._LoadMoreBtn();
            this._ReadMoreReadLess();
            if(this.$el.find("#selection_category_box").length){
                this.$el.find("#selection_category_box").select2();
            }
            if(this.$el.find("input#hiderrpcheckbox").length){
                this.$el.find("input#hiderrpcheckbox").switchify();
            }
            if(this.$el.find("input#instockcheckbox").length){
                this.$el.find("input#instockcheckbox").switchify();
            }
            if(this.$el.find("input#hideproductpricecheckbox").length){
                this.$el.find("input#hideproductpricecheckbox").switchify();
            }
            if(this.$el.find("#planned_delivery_date").length){
                this.datepickerinitlize();
            }
            if(this.$el.find('#b2b_products')){
                // this.cartTable();
            }
            this.$el.find('[data-toggle="popover"]').popover({
                placement: 'auto'
            });
            return Promise.all(defs);
        },
        cartTable:function(){
            // this.$el.find('#b2b_products').removeClass('stacktable');
            // if($('.stacktable').length){
            //     $('.stacktable').parent().remove();
            // }
            // this.$el.find('#b2b_products').cardtable();
            this.trigger_up('widgets_start_request', {
                $target: $('.b2b-product-quick-view-action'),
            });
        },
        datepickerinitlize: function(){
            let newdate = new Date(this.$el.find("#planned_delivery_date").data('default_date'));
            var holydays = [];

            function highlightDays(date) {
                for (var i = 0; i < holydays.length; i++) {
                    if (new Date(holydays[i]).toString() == date.toString()) {
                        return [true, 'highlight'];
                    }
                }
                return [true, ''];

            }
            var disabledDays = this.$el.find("#planned_delivery_date").data('holidays');
            function disableAllTheseDays(date) {
                var dbdate = moment(date).format('MM-DD-YYYY');
                if (disabledDays) {
                    for (var i = 0; i < disabledDays.length; i++) {
                        if($.inArray(dbdate,disabledDays) != -1) {
                            return [false];
                        }
                    }
                }
                return [true];
            }
            function setCustomDate(date) {
                var clazz = "";
                var arr1 = highlightDays(date);
                if (arr1[1] != "") clazz = arr1[1];

                var arr2 = disableAllTheseDays(date);
                var arr3 = $.datepicker.noWeekends(date);

                return [(!arr2[0] || !arr3[0]) ? false : true, clazz];
            }
            // this.$el.find("#planned_delivery_date").datepicker({
            //     defaultDate: newdate,
            //     minDate: newdate,
            //     changeMonth: true,
            //     numberOfMonths: 1,
            //     beforeShowDay: setCustomDate,
            //     dateFormat: 'dd.mm.yy',
            //     onSelect: async function(dateText) {
            //         $.ajax({
            //           type: "GET",
            //           url: '/b2b/set/planned/date',
            //           data: {'planeddate': dateText},
            //           success: function (page) {
            //           }
            //         });
            //     }
            // });
        },
        _onChangeDelivery_date: function(ev){
            var planned_delivery_date = this.$el.find("#planned_delivery_date")
            $.ajax({
              type: "GET",
              url: '/b2b/set/planned/date',
              data: {'planeddate': ev.currentTarget.value},
              success: function (page) {
              }
            });
        },
        OnScanB2BProducts: function(ev){
            var self = this
            // qweb.add_template('/web_enterprise/static/src/webclient/barcode/barcode_scanner.xml');
            // const barcode = await BarcodeScanner.scanBarcode();
            $('.scan_barcode_popup').modal('show');
            let html5QrcodeScanner = new Html5QrcodeScanner(
              "reader",
              { fps: 30, qrbox: {width: 500, height: 500} },
              /* verbose= */ false);
            html5QrcodeScanner.render(onScanSuccess, onScanFailure)
            function onScanSuccess(decodedText, decodedResult) {
                // handle the scanned code as you like, for example:
                console.log(`Code matched = ${decodedText}`, decodedResult);
                self._rpc({
                route: "/b2b/product/fetch_barcode",
                params: {
                    barcode: decodedText,
                },
                }).then(function (product) {
                    if(product != undefined){
                        html5QrcodeScanner.clear()
                        $('.scan_barcode_popup').modal('hide');
                        var product_quickview_str = 'a[data-variant-id='+ product + ']'
                        $(product_quickview_str).click()
                    }
                });
            }
            function onScanFailure(error) {
              // handle scan failure, usually better to ignore and keep scanning.
              // for example:
                console.warn(`Code scan error = ${error}`);
            }
        },
        // working........
        _onSubmitProductSearch: function (ev) {
            var self = this;
            var brand_id = parseInt($('input[name="brand_id"]').val())
            var search = $('.b2b_o_wsale_products_searchbar_form input[name="search"]').val()
            this._rpc("/b2b/brand/update_json",{
                brand: brand_id,
                search: search,
            }).then(function (data) {
                if(data && data['b2b_product_order_line'] != undefined){
                    $(".o_wsale_b2b_products_table_wrapper #b2b_products").html(data['b2b_product_order_line']);
                    if(data && data['b2b_product_order_line_mobile_view'] != undefined){
                        $(".o_wsale_b2b_products_table_wrapper .b2b_moble_view tbody").html(data['b2b_product_order_line_mobile_view']);
                    }
                    $('.tp-load-more-products-container').remove();
                    $('.products_pager').remove();
                    // self.ajaxLoadOnClick = odoo.dr_theme_config.json_lazy_load_config.enable_ajax_load_products_on_click;
                    self.$pager = $('.products_pager');
                    self.$tpRTargetElement = $('#wrapwrap'); // #wrapwrap for now bcoz window is not scrolleble in v14
                    if (self.$pager.children().length && self.$('.o_wsale_b2b_products_table_wrapper tbody tr:last').length) {
                        self.$pager.addClass('d-none');
                        self._setState();
                        $(renderToElement('tp_load_more_products_template')).appendTo(self.$('.o_wsale_b2b_products_table_wrapper'));
                        $($('.tp-load-more-products-container')[1]).removeClass('d-flex')
                        $($('.tp-load-more-products-container')[1]).addClass('d-none')
                    }
                }
                self.cartTable();
            });
        },
        // working....
        _onKeyUpProductSearchInput: function (ev) {
            var self = this;
            if (ev.which === 13){
                var brand_id = parseInt($('input[name="brand_id"]').val())
                var search = ev.currentTarget.value
                this._rpc("/b2b/brand/update_json",{
                        brand: brand_id,
                        search: search,
                }).then(function (data) {
                    if(data && data['b2b_product_order_line'] != undefined){
                        $(".o_wsale_b2b_products_table_wrapper #b2b_products").html(data['b2b_product_order_line']);
                        if(data && data['b2b_product_order_line_mobile_view'] != undefined){
                            $(".o_wsale_b2b_products_table_wrapper .b2b_moble_view tbody").html(data['b2b_product_order_line_mobile_view']);
                        }
                        $('.tp-load-more-products-container').remove();
                        $('.products_pager').remove();
                        self.ajaxLoadOnClick = odoo.dr_theme_config.json_lazy_load_config.enable_ajax_load_products_on_click;
                        self.$pager = $('.products_pager');
                        if (self.$pager.children().length && self.$('.o_wsale_b2b_products_table_wrapper tbody tr:last').length) {
                            self.$pager.addClass('d-none');
                            self._setState();
                            $(renderToElement('theme_prime.Loader')).appendTo(self.$('.o_wsale_b2b_products_table_wrapper'));
                            $($('.tp-load-more-products-container')[1]).removeClass('d-flex')
                            $($('.tp-load-more-products-container')[1]).addClass('d-none')
                        }
                    }
                    self.cartTable();
                });
            }
        },
        _LoadMoreBtn: function () {
            var self = this;
            this.$pager = $('.products_pager');
            if (this.$pager.children().length && this.$('.o_wsale_b2b_products_table_wrapper tbody tr:last').length) {
                // this.$pager.addClass('d-none');
                this._setState();
                // $(renderToElement('theme_prime.Loader')).appendTo(self.$('.o_wsale_b2b_products_table_wrapper'));
            }
        },
        _setState: function () {
            this.$lastLoadedProduct = this.$('.o_wsale_b2b_products_table_wrapper #b2b_products tbody tr:last');
            this.$productsContainer = this.$('.o_wsale_b2b_products_table_wrapper #b2b_products tbody');
            this.$lastLoadedProduct_mobile = this.$('.o_wsale_b2b_products_table_wrapper .b2b_moble_view tbody tr:last');
            this.$productsContainer_mobile = this.$('.o_wsale_b2b_products_table_wrapper .b2b_moble_view tbody');
            this.readyNextForAjax = true;
            this.pageURL = this.$pager.find('li:last a').attr('href');
            this.lastLoadedPage = 1;
            this.totalPages = parseInt(this.$target.get(0).dataset.totalPages);
        },
        _ReadMoreReadLess: function () {
            
        },
        _loadAndAppendProducts: function () {
            console.log("......... call _loadAndAppendProducts.....")
            var self = this;
            this.readyNextForAjax = false;
            var newPage = self.lastLoadedPage + 1;
            this.loadedpage = newPage;
            $.ajax({
                url: this.pageURL,
                type: 'GET',
                beforeSend: function () {
                    $(renderToElement('droggol_default_loader')).appendTo(self.$('.o_wsale_b2b_products_table_wrapper'));
                },
                success: function (page) {
                    self.$('.d_spinner_loader').remove();
                    self.$('.tp-load-more-btn').removeClass('disabled');
                    if ($('.b2b_moble_view').length && $('.b2b_moble_view').length != undefined) {
                        let $renderedPage_mobile = $(page);
                        let $productsToAdd_mobile = $renderedPage_mobile.find(".product_list_page .o_wsale_b2b_products_table_wrapper .b2b_moble_view tr:gt(0)");

                        $productsToAdd_mobile.each(function() {
                            if ($('.b2b_rs_filter_view input[name="hiderrpcheckbox"]').is(":checked")){
                                $(this).find('.toggle_hide_show_rrp').addClass('d-none')
                            }
                        })
                        $productsToAdd_mobile.each(function() {
                            if ($('.b2b_rs_filter_view input[name="hideproductpricecheckbox"]').is(":checked")){
                                $(this).find('.toggle_hide_show_product_price').addClass('d-none')
                            }
                        })

                        self.$productsContainer_mobile.append($productsToAdd_mobile);
                        self.readyNextForAjax = true;
                        self.$lastLoadedProduct_mobile = self.$('.o_wsale_b2b_products_table_wrapper .b2b_moble_view tbody tr:last');
                        self.lastLoadedPage = newPage;
                        self.pageURL = $renderedPage_mobile.find('.products_pager li:last a').attr('href');
                        if ($renderedPage_mobile.find('.products_pager li:last').hasClass('disabled')) {
                            $(renderToElement('dr_all_products_loaded')).appendTo(self.$('.o_wsale_b2b_products_table_wrapper'));
                            self.$('.tp-load-more-products-container').append();
                        }
                    }
                    if ($('#b2b_products').length && $('#b2b_products').length != undefined) {
                        let $renderedPage = $(page);
                        let $productsToAdd = $renderedPage.find(".product_list_page .o_wsale_b2b_products_table_wrapper table#b2b_products tr:gt(0)");

                        $productsToAdd.each(function() {
                            if ($('.b2b_rs_filter_view input[name="hiderrpcheckbox"]').is(":checked")){
                                $(this).find('.toggle_hide_show_rrp').addClass('d-none')
                            }
                        })
                        $productsToAdd.each(function() {
                            if ($('.b2b_rs_filter_view input[name="hideproductpricecheckbox"]').is(":checked")){
                                $(this).find('.toggle_hide_show_product_price').addClass('d-none')
                            }
                        })

                        self.$productsContainer.append($productsToAdd);
                        self.readyNextForAjax = true;
                        self.$lastLoadedProduct = self.$('.o_wsale_b2b_products_table_wrapper #b2b_products tbody tr:last');
                        self.lastLoadedPage = newPage;
                        self.pageURL = $renderedPage.find('.products_pager li:last a').attr('href');
                        if ($renderedPage.find('.products_pager li:last').hasClass('disabled')) {
                            $(renderToElement('dr_all_products_loaded')).appendTo(self.$('.o_wsale_b2b_products_table_wrapper'));
                            self.$('.tp-load-more-products-container').remove();
                        }
                    }
                    self.cartTable();
                    self._ReadMoreReadLess();
                }
            });
        },
        _onClickLoadMoreProductsBtn: function (ev) {
            this._loadAndAppendProducts();
        },
        _onClickReadMore: function(event){
            var moretext = _t("Read More");
            var lesstext = _t("Read Less");
            if ($(event.currentTarget).hasClass("less")) {
                $(event.currentTarget).removeClass("less");
                $(event.currentTarget).html(moretext);
            } else {
                $(event.currentTarget).addClass("less");
                $(event.currentTarget).html(lesstext);
            }
            $(event.currentTarget).parent().prev().toggle();
            $(event.currentTarget).prev().toggle();
            return false;
        },
        _onSubmitSaleSearch: function (ev) {
            return;
        },
        onClickAddCartJSON: function (ev) {
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            var $input = $link.closest('.input-group').find("input");
            var min = parseFloat($input.data("min") || 0);
            var max = parseFloat($input.data("max") || Infinity);
            var previousQty = parseFloat($input.val() || 0, 10);
            var quantity = ($link.has(".fa-minus").length ? -1 : 1) + previousQty;
            var newQty = quantity > min ? (quantity < max ? quantity : max) : min;

            if (newQty !== previousQty) {
                $input.val(newQty).trigger('change');
            }
            return false;
        },
        _get_URL: function(url, ppg){
            if(url.includes('?')) {
                return window.location.href + '&ppg='+ppg;
            }else{
                return window.location.href + '?ppg='+ppg;
            }
        },
        _onChangeHideRrpCheckBox: function(ev){
            console.log("........hideproductpricecheckbox")
            var self = this;
            var $input = $(ev.currentTarget);
            $('.toggle_hide_show_rrp').toggleClass('d-none')
        },
        // working.........
        _onChangehideproductpricecheckbox: function(ev){
            var self = this;
            var $input = $(ev.currentTarget);
            $('.toggle_hide_show_product_price').toggleClass('d-none')
        },
        _onChangeb2bquickQuantity: function(ev){
            var self = this;
            var $input = $(ev.currentTarget);
            var line_id = parseInt($input.data('line-id'), 10);
            var added_qty = $(ev.currentTarget).closest('.js_product').find("input[name='trade_unit_of_product']").val();
            var trade_unit_of_product = $(ev.currentTarget).closest('.js_product').find("input[name='add_quick_qty']").val();
            var add_qty = parseInt(added_qty)*parseInt(trade_unit_of_product)
            $(ev.currentTarget).closest('.js_product').find("input[name='add_qty']").val(add_qty);
            $(ev.currentTarget).closest('.js_product').find("#quick_view_total_units .total_unit_qty").text(add_qty);
        },

        _onChangeb2bcartQuantity: function(ev){
            var self = this;
            var $input = $(ev.currentTarget);
            if ($input.data('update_change')) {
                return;
            }
            var value = parseInt($input.val() || 0, 10);
            if (isNaN(value)) {
                value = 0
            }
            var line_id = parseInt($input.data('line-id'), 10);
            // var productID = parseInt($input.data('product-id'), 10);
            // debugger;
            this._rpc("/b2b/cart/update_json",{
                line_id: line_id,
                product_id: parseInt($input.data('product-id'), 10),
                set_qty: value
            }).then(function (data) {
                if(data && data['b2b_product_order_line'] != undefined && data['b2b_product_order_line_product_id'] != undefined){
                    $("#b2b_product_item_id_"+ data['b2b_product_order_line_product_id']).replaceWith(data['b2b_product_order_line']);
                }
                if(data && data['b2b_cart_line'] != undefined && data['b2b_product_order_line_product_id'] != undefined){
                    $("#b2b_order_id_"+ data['b2b_cart_line_id']).replaceWith(data['b2b_cart_line']);
                }
                if(data && data['b2b_product_order_line_mobile_view'] != undefined && data['b2b_product_order_line_product_id'] != undefined){
                    $(".b2b_moble_view #b2b_product_item_id_"+ data['b2b_product_order_line_product_id']).replaceWith(data['b2b_product_order_line_mobile_view']);
                }
                if(data && data['b2b_order_total'] != undefined){
                    $('.b2b_shop_total_cl h3').replaceWith(data['b2b_order_total']);
                }
                if(data && data['free_delivery_msg'] != undefined){
                    $('.b2b_check_free_delivery_cl h3').html(data['free_delivery_msg'])
                }
                self.cartTable();
            });
        },
        // working.......
        _onChangeSetQuantity: function(ev){
            var self = this;
            var $input = $(ev.currentTarget);
            if ($input.data('update_change')) {
                return;
            }
            var value = parseInt($input.val() || 0, 10);
            if (isNaN(value)) {
                value = 0
            }
            var line_id = parseInt($input.data('line-id'), 10);
            // var productID = parseInt($input.data('product-id'), 10);
            // debugger;
            this._rpc("/b2b/cart/update_json", {
                line_id: line_id,
                product_id: parseInt($input.data('product-id'), 10),
                set_qty: value
            }).then(function (data) {
                if(data && data['b2b_product_order_line'] != undefined && data['b2b_product_order_line_product_id'] != undefined){
                    $("#b2b_product_item_id_"+ data['b2b_product_order_line_product_id']).replaceWith(data['b2b_product_order_line']);
                    $(".popover_warning").popover({
                        placement: 'auto'
                    });
                    if ($('.b2b_rs_filter_view input[name="hiderrpcheckbox"]').is(":checked")){
                        $('#b2b_products').find('.toggle_hide_show_rrp').addClass('d-none')
                    }
                    if ($('.b2b_rs_filter_view input[name="hideproductpricecheckbox"]').is(":checked")){
                        $('#b2b_products').find('.toggle_hide_show_product_price').addClass('d-none')
                    }
                }
                if(data && data['b2b_product_order_line_mobile_view'] != undefined && data['b2b_product_order_line_product_id'] != undefined){
                    $(".b2b_moble_view #b2b_product_item_id_"+ data['b2b_product_order_line_product_id']).replaceWith(data['b2b_product_order_line_mobile_view']);
                }
                if(data && data['b2b_product_order_line_mobile_view'] != undefined && data['b2b_product_order_line_product_id'] != undefined){
                    $(".b2b_moble_view #b2b_product_item_id_"+ data['b2b_product_order_line_product_id']).replaceWith(data['b2b_product_order_line_mobile_view']);
                    if ($('.b2b_rs_filter_view input[name="hiderrpcheckbox"]').is(":checked")){
                        $('.b2b_moble_view').find('.toggle_hide_show_rrp').addClass('d-none')
                    }
                    if ($('.b2b_rs_filter_view input[name="hideproductpricecheckbox"]').is(":checked")){
                        $('.b2b_moble_view').find('.toggle_hide_show_product_price').addClass('d-none')
                    }
                }
                if(data && data['b2b_order_total'] != undefined){
                    $('.b2b_shop_total_cl h3').replaceWith(data['b2b_order_total']);
                }
                if(data && data['free_delivery_msg'] != undefined){
                    $('.b2b_check_free_delivery_cl h3').html(data['free_delivery_msg'])
                }
                if(data && data['cart_quantity'] != undefined){
                    $("#print_invoice_report").attr('data-cart_qty', data['cart_quantity']);
                }else{
                    $("#print_invoice_report").attr('data-cart_qty', 0);
                }
                self.cartTable();
            });
        },
        _onChangeSetNote: function(ev){
            var self = this;
            var $input = $(ev.currentTarget);
            var line_id = parseInt($input.data('line-id'), 10);
            var note = $input.val();
            this._rpc("/b2b/update_note",{
                    line_id: line_id,
                    note: note
            }).then(function (data) {

            });
        }
    });

    publicWidget.registry.B2BPortalComman = publicWidget.Widget.extend({
        selector: '.b2b_portal_comman',
        events: {
            'click .a-submit': '_onClickSubmit',
            'change select[name="country_id"]': '_onChangeCountry'
        },
        init: function () {
            this._super.apply(this, arguments);
            this._changeCountry = debounce(this._changeCountry.bind(this), 500);
            this._rpc = this.bindService("rpc");
        },
        start() {
            const def = this._super(...arguments);
            this.$('select[name="country_id"]').change();
            return def;
        },
        _onClickSubmit:function (ev, forceSubmit) {
            var $aSubmit = $(ev.currentTarget);
            ev.preventDefault();
            $aSubmit.closest('form').submit();
        },
        _onChangeCountry: function (ev) {
            if (!this.$('.checkout_autoformat').length) {
                return;
            }
            this._changeCountry();
        },
        _changeCountry: function () {
            if (!$("#country_id").val()) {
                return;
            }
            this._rpc("/shop/country_infos/" + $("#country_id").val(), {
                    mode: $("#country_id").attr('mode'),
            }).then(function (data) {
                // placeholder phone_code
                $("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');

                // populate states and display
                var selectStates = $("select[name='state_id']");
                // dont reload state at first loading (done in qweb)
                if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
                    if (data.states.length || data.state_required) {
                        selectStates.html('');
                        $.each(data.states, function (x) {
                            var opt = $('<option>').text(x[1])
                                .attr('value', x[0])
                                .attr('data-code', x[2]);
                            selectStates.append(opt);
                        });
                        selectStates.parent('div').show();
                    } else {
                        selectStates.val('').parent('div').hide();
                    }
                    selectStates.data('init', 0);
                } else {
                    selectStates.data('init', 0);
                }

                // manage fields order / visibility
                if (data.fields) {
                    if ($.inArray('zip', data.fields) > $.inArray('city', data.fields)){
                        $(".div_zip").before($(".div_city"));
                    } else {
                        $(".div_zip").after($(".div_city"));
                    }
                    var all_fields = ["street", "zip", "city", "country_name"]; // "state_code"];
                    $.each(all_fields, function (field) {
                        $(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields)>=0);
                    });
                }

                if ($("label[for='zip']").length) {
                    $("label[for='zip']").toggleClass('label-optional', !data.zip_required);
                    $("label[for='zip']").get(0).toggleAttribute('required', !!data.zip_required);
                }
                if ($("label[for='zip']").length) {
                    $("label[for='state_id']").toggleClass('label-optional', !data.state_required);
                    $("label[for='state_id']").get(0).toggleAttribute('required', !!data.state_required);
                }
            });
        }
    });

    publicWidget.registry.B2bShopwebsiteSaleCart = publicWidget.Widget.extend({
        selector: '.b2b_portal_shop .oe_cart, .b2b_cart_view_page .oe_cart',
        events: {
            'click .js_change_shipping': '_onClickChangeShipping',
            'click .js_edit_address': '_onClickEditAddress'
        },
        _onClickChangeShipping: function (ev) {
            var $old = $('.all_shipping').find('.card.border.border-primary');
            $old.find('.btn-ship').toggle();
            $old.addClass('js_change_shipping');
            $old.removeClass('border border-primary');

            var $new = $(ev.currentTarget).parent('div.one_kanban').find('.card');
            $new.find('.btn-ship').toggle();
            $new.removeClass('js_change_shipping');
            $new.addClass('border border-primary');

            var $form = $(ev.currentTarget).parent('div.one_kanban').find('form.d-none');
            $.post($form.attr('action'), $form.serialize()+'&xhr=1');
        },
        _onClickEditAddress: function (ev) {
            ev.preventDefault();
            $(ev.currentTarget).closest('div.one_kanban').find('form.d-none').attr('action', '/b2b/address').submit();
        }
    });
    

    publicWidget.registry.B2bCartview = publicWidget.Widget.extend(VariantMixin, cartHandlerMixin, {
        selector: '.b2b_cart_view_page',
        events: $.extend({}, VariantMixin.events || {}, {
            'change .oe_cart input.js_quantity[data-product-id]': '_onChangeCartQuantity',
            'click a.js_add_cart_json': '_onClickAddCartJSON',
            'click a.js_delete_product': '_onRemoveQtyLine',
            'click .show_coupon': '_onClickShowCoupon_b2b'

        }),
        init: function () {
            this._super.apply(this, arguments);
            this._rpc = this.bindService("rpc");
        },
        _onClickAddCartJSON: function (ev){
            this.onClickAddCartJSON(ev);
        },
        _onChangeCartQuantity: function (ev) {
            var $input = $(ev.currentTarget);
            if ($input.data('update_change')) {
                return;
            }
            var value = parseInt($input.val() || 0, 10);
            if (isNaN(value)) {
                value = 1;
            }
            var $dom = $input.closest('tr');
            // var default_price = parseFloat($dom.find('.text-danger > span.oe_currency_value').text());
            var $dom_optional = $dom.nextUntil(':not(.optional_product.info)');
            var line_id = parseInt($input.data('line-id'), 10);
            var productIDs = [parseInt($input.data('product-id'), 10)];
            this._changeCartQuantity($input, value, $dom_optional, line_id, productIDs);
        },
        _onRemoveQtyLine: function(ev){
            ev.preventDefault();
            $(ev.currentTarget).closest('tr').find('.js_quantity').val(0).trigger('change');
        },
        _changeCartQuantity: function ($input, value, $dom_optional, line_id, productIDs) {
            $.each($dom_optional, function (elem) {
                $(elem).find('.js_quantity').text(value);
                productIDs.push($(elem).find('span[data-product-id]').data('product-id'));
            });
            $input.data('update_change', true);

            this._rpc("/b2b/cart/update_json",{
                line_id: line_id,
                product_id: parseInt($input.data('product-id'), 10),
                set_qty: value
            }).then(function (data) {
                $input.data('update_change', false);
                var check_value = parseInt($input.val() || 0, 10);
                if (isNaN(check_value)) {
                    check_value = 1;
                }
                if (!data.cart_quantity) {
                    return window.location = '/b2b/cart';
                }
                $input.val(data.quantity);
                $('.js_quantity[data-line-id='+line_id+']').val(data.quantity).text(data.quantity);

                // $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();
                $(".js_cart_summary").first().before(data['b2b_portal.b2b_short_cart_summary']).end().remove();
                // wSaleUtils.updateCartNavBar(data);
                if (data.quantity == 0) {
                    location.reload();
                }
                wSaleUtils.showWarning(data.warning);
            });
        },
        _onClickShowCoupon_b2b: function (ev) {
            $(ev.currentTarget).hide();
            $('.coupon_form').removeClass('d-none');
        },
    });

    publicWidget.registry.B2BProductDetailsPage = publicWidget.Widget.extend({
        selector: '.b2b_product_details_view_page',
        events: {
            'click button#add_cart': 'AddToCart',
        },
        init: function () {
            this._super.apply(this, arguments);
            this._rpc = this.bindService("rpc");
        },
        start() {
            const def = this._super(...arguments);
            return def;
        },
        AddToCart: function(ev) {
            var product_id = $("form#product").find('input[name="product_id"]').val();
            var add_qty = $("form#product").find('input[name="add_qty"]').val();

            this._rpc("/b2b/cart/update_json", {
                    product_id: parseInt(product_id, 10),
                    add_qty: parseInt(add_qty, 10),
            }).then(function (data) {
                if (data.success) {
                    $(".add_success")
                        .text("Product added into " + data.sale_order)
                        .fadeIn(1000);
                    setTimeout(function() {
                        window.location.reload();
                    }, 2000);
                }
            });
        },
    });
    
    publicWidget.registry.B2BCartPage = publicWidget.Widget.extend({
        selector: '.b2b_cart_view_page',
        events: {
            'click #enable': '_onClickEnable',
            'click .placeorder_event_elment': '_onHightlightbutton',
            'mouseout .placeorder_event_elment': '_mouseoutelemt'
        },
        _onClickEnable: function(event){
            var button = $(event.currentTarget).closest('.b2b_cart_view_page').find(".b2b_placeorder_btn");
            if (button.hasClass('disabled')) {
                button.removeClass('disabled');
                $('.placeorder_event_elment').removeClass('disable_placeholder')
            } else {
                button.addClass('disabled');
                $('.placeorder_event_elment').addClass('disable_placeholder')
            }
        },
        _onHightlightbutton: function(ev){
            if($(ev.currentTarget).hasClass('disable_placeholder')){
                $('.checkbox_mssg').addClass('binktermblink');
            }
        },
        _mouseoutelemt: function(ev){
            $('.checkbox_mssg').removeClass('binktermblink');
        }
    });

