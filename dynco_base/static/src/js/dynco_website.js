odoo.define('dynco_base.dynco_website', function(require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var sAnimations = require('website.content.snippets.animation');

    sAnimations.registry.HeaderHamburgerDynco = sAnimations.Class.extend({
        selector: '#wrapwrap',
        effects: [{
            startEvents: 'scroll',
            update: '_updateHeaderOnScroll',
        }],
        read_events: {
            'click .header_hamburger_dynco': 'HamburgerClick',
            // 'wheel': '_onMouseWheel',
        },

        init: function () {
            this._super.apply(this, arguments);

            this.scrollingDownwards = true;
            this.hiddenHeader = false;
            this.position = 0;
            this.atTop = true;
            this.checkPoint = 0;
            this.scrollOffsetLimit = 200;
        },
        start: function () {
            return this._super.apply(this, arguments);
        },
        HamburgerClick: function(ev){
            $(ev.currentTarget).closest('#wrapwrap').find('header.knk_dynco_header_custom nav.navbar').css('display', 'block');
        },
        // _onMouseWheel: function(ev){
        //     // $(ev.currentTarget).closest('#wrapwrap').find('header.knk_dynco_header_custom nav.navbar').css('display', 'none');
        // },
        /**
         * @private
         */
        _computeTopGap() {
            return 0;
        },
        _updateHeaderOnScroll: function (scroll) {
            this.topGap = this._computeTopGap();
            const scrollingDownwards = (scroll > this.position);
            const atTop = (scroll <= 0);
            if (scrollingDownwards !== this.scrollingDownwards) {
                this.checkPoint = scroll;
            }

            this.scrollingDownwards = scrollingDownwards;
            this.position = scroll;
            this.atTop = atTop;

            if (scrollingDownwards) {
                $('#wrapwrap').find('header.knk_dynco_header_custom nav.navbar').css('display', 'none');
                $('#wrapwrap').find('header.knk_dynco_header_custom.o_header_is_scrolled nav.navbar').css('display', 'none');
                if (!this.hiddenHeader && scroll - this.checkPoint > (this.scrollOffsetLimit + this.topGap)) {
                    $('#wrapwrap').find('header.knk_dynco_header_custom nav.navbar').css('display', 'none');
                    $('#wrapwrap').find('header.knk_dynco_header_custom.o_header_is_scrolled nav.navbar').css('display', 'none');
                    this.hiddenHeader = true;
                }
            } else {
                $('#wrapwrap').find('header.knk_dynco_header_custom nav.navbar').css('display', 'block');
                $('#wrapwrap').find('header.knk_dynco_header_custom.o_header_is_scrolled nav.navbar').css('display', 'block');
                if (this.hiddenHeader && scroll - this.checkPoint < -(this.scrollOffsetLimit + this.topGap) / 2) {
                    $('#wrapwrap').find('header.knk_dynco_header_custom nav.navbar').css('display', 'block');
                    $('#wrapwrap').find('header.knk_dynco_header_custom.o_header_is_scrolled nav.navbar').css('display', 'block');
                    this.hiddenHeader = false;
                }
            }
            if (atTop && this.atTop) {
                $('#wrapwrap').find('header.knk_dynco_header_custom nav.navbar').css('display', 'none');
                $('#wrapwrap').find('header.knk_dynco_header_custom.o_header_is_scrolled nav.navbar').css('display', 'none');
                // Force reshowing the invisible-on-scroll sections when reaching
                // the top again
            }
        },

    });

})
