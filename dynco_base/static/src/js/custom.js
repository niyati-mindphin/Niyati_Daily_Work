odoo.define('dynco_base.custom', function(require) {
    'use strict';

    const config = require('web.config');
    var suggested_product_slider = require('theme_prime.suggested_product_slider');
    var dynamic_snippets = require('theme_prime.dynamic_snippets');
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var sAnimations = require('website.content.snippets.animation');
    const RootWidgetSetClass = require('theme_prime.product.root.widget');
    const NewCartSidebar = require('theme_prime.sidebar');

    publicWidget.registry.WebsiteSale.include({
        _addToCartInPage: function(params){
            var self = this;
            return this._super(...arguments).then(function(data){
                new NewCartSidebar.CartSidebar(self).open();
            });
        },
    });

    publicWidget.registry.onScrollTopToBottomDynco = publicWidget.Widget.extend({
        selector: 'a.dynco_scroll_top_to_botton',
        events:{
            'click':'onscrolltoptobottompage'
        },
        start: function () {
            return this._super.apply(this, arguments);
        },
        onscrolltoptobottompage: function(ev){
            // $("#wrapwrap").animate({ scrollTop: $("#wrapwrap").prop('scrollHeight') }, 2000);
            $('#wrapwrap').animate({ scrollTop: $("section.s_image_gallery:first").offset().top}, 'slow');
        }
    });

    publicWidget.registry.OnClickHideShowBtn = publicWidget.Widget.extend({
        selector: '#product_detail .webshop_marketing_text',
        events:{
            'click .read_more_less_btn .read_more_btn': '_onClickReadMore',
            'click .read_more_less_btn .read_less_btn': '_onClickReadLess',
        },
        start: function () {
            var divheight = $('.product_text_div').height();
            var lineheight = $('.product_text_div').css('line-height');
            var total_lines = Math.round(divheight/parseInt(lineheight));
            // if (total_lines > 15) {
            //     $('.webshop_marketing_text').find('.product_text_div').addClass('text_limited_lines');
            // } else {
            //     $('.webshop_marketing_text').find('.read_more_less_btn').addClass('d-none');
            // }
            return this._super.apply(this, arguments);
        },
        _onClickReadMore: function(ev){
            $(ev.currentTarget).addClass('d-none');
            $(ev.currentTarget).parent().find('.read_less_btn').removeClass('d-none');
            $(ev.currentTarget).closest('.webshop_marketing_text').find('.product_text_div').removeClass('text_limited_lines');
        },
        _onClickReadLess: function(ev){
            $(ev.currentTarget).addClass('d-none');
            $(ev.currentTarget).parent().find('.read_more_btn').removeClass('d-none');
            $(ev.currentTarget).closest('.webshop_marketing_text').find('.product_text_div').addClass('text_limited_lines');
        }
    });

    publicWidget.registry.TpSuggestedProductSlider.prototype.xmlDependencies.push('/dynco_base/static/src/xml/suggested_product_slider_inherit.xml');
    publicWidget.registry.s_d_products_snippet.prototype.xmlDependencies.push('/dynco_base/static/src/xml/cards_inherit.xml');

    publicWidget.registry.FixedHeader.include({
        _updateHeaderOnScroll: function (scroll) {
            if (scroll > (this.scrolledPoint + this.topGap)) {
                if (!this.$el.hasClass('o_header_affixed')) {
                    this.$el.css('transform', `translate(0, -${this.topGap}px)`);
                    void this.$el[0].offsetWidth; // Force a paint refresh
                    this._toggleFixedHeader(true);
                }
            } else {
                this._toggleFixedHeader(false);
                void this.$el[0].offsetWidth; // Force a paint refresh
                this.$el.css('transform', '');
            }
        }
    });

    RootWidgetSetClass.include({
        _setClass: function () {
            this.deviceSizeClass = config.device.size_class;
            if (this.deviceSizeClass <= 1) {
                this.cardSize = 6;
                this.cardColClass = 'col-' + this.cardSize.toString();
            } else if (this.deviceSizeClass === 2) {
                this.cardSize = 6;
                this.cardColClass = 'col-sm-' + this.cardSize.toString();
            } else if (this.deviceSizeClass === 3 || this.deviceSizeClass === 4) {
                this.cardSize = 4;
                this.cardColClass = 'col-md-' + this.cardSize.toString();
            } else if (this.deviceSizeClass >= 5) {
                this.cardSize = parseInt(12 / this.uiConfigInfo.ppr);
                this.cardColClass = 'col-lg-' + this.cardSize.toString();
            }
        }
    });


    sAnimations.registry.AddToCartAvailProduct = sAnimations.Class.extend({
        selector: '#product_detail',
        read_events: {
            'click .dynco_avail_variants #available_add_to_cart': 'onAddToCartClick',
        },

        init: function () {
            this._super.apply(this, arguments);
        },
        start: function () {
            return this._super.apply(this, arguments);
        },
        onAddToCartClick: function(ev){
            var product_id = $(ev.currentTarget).closest('.dynco_cart').find('input[name="product_id"]').val();

            ajax.jsonRpc('/webshop/cart/update_json', 'call', {
                product_id: product_id,
            }).then(function() {
                window.location = '/shop/cart';
            });
        },

    });
});

$(document).ready(function() {
    $('#dynamic_rating_homepage').on('reload', function(e) {
        this._rpc({
            model: 'website',
            method: 'get_rating_from_all_products',
        }).then(function (result) {
            $("t[t-set='rating_ids']").val(result);
        })
    });

    $('.category_slider').on('reload', function(e) {
        location.reload(true);
    });
 });

$(document).ready(function() {
    $("h2 > span, h2 > font, h2 > a").parent().addClass('h2notapply');
	$('.product_video_popup_le').owlCarousel({
        animateOut: 'fadeOut',
        animateIn: 'fadeIn',
        responsive:{
            0:{
                items:1
            },
            500:{
                items:1
            },
            700:{
                items:1
            },
            900:{
                items:1
            }
        },
        smartSpeed:450,
        nav:true,
        loop:true,
    });

    $('.ecommerce_categ_product').owlCarousel({
        loop:true,
        nav:true,
        dots:false,
        margin:10,
        responsiveClass:true,
        smartSpeed:400,
        autoplay:true,
        responsive:{
            0:{
                items:1,
            },
            600:{
                items:3,
            },
            1000:{
                items:5,
            }
        },
        navText: ['<i class="dri dri-arrow-left-l"></i>', '<i class="dri dri-arrow-right-l"></i>'],
    })

    var $videoSrc_le;
    $('.video_play_url_main_popup_cl_le').click(function() {
        $videoSrc_le = $(this).data("src");
        $('#myModalvideopopupcl').modal('show');
    });
    $('#myModalvideopopupcl').on('shown.bs.modal', function (e) {
        $("#myModalvideopopupcl #video").attr('src',$videoSrc_le + "?autoplay=1&amp;modestbranding=1&amp;showinfo=0" );
    });
    $('#myModalvideopopupcl').on('hide.bs.modal', function (e) {
        $("#myModalvideopopupcl #video").attr('src',$videoSrc_le);
    });
    $('.on_popup_when_leave .modal').on('show.bs.modal', function (e) {
        if (window.matchMedia('(max-width: 576px)').matches) {
            $(e.currentTarget).modal('hide')
        }
    });
    $(window).on('shown.bs.modal', function (ev) {
        if ($('.b2b_rs_filter_view input[name="hiderrpcheckbox"]').is(":checked")){
            $('.b2b_quick_view_qty_update').find('.toggle_hide_show_rrp').addClass('d-none')
        }
        if ($('.b2b_rs_filter_view input[name="hideproductpricecheckbox"]').is(":checked")){
            $('.b2b_quick_view_qty_update').find('.toggle_hide_show_product_price').addClass('d-none')
        }
    });
});
