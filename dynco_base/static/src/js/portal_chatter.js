odoo.define('dynco_base.portal_chatter', function (require) {
'use strict';

var core = require('web.core');
var portalChatter = require('portal.chatter');
var utils = require('web.utils');
var time = require('web.time');

var _t = core._t;
var PortalChatter = portalChatter.PortalChatter;
var qweb = core.qweb;

/**
 * PortalChatter
 *
 * Extends Frontend Chatter to handle rating
 */
PortalChatter.include({
    events: _.extend({}, PortalChatter.prototype.events, {
    }),
    xmlDependencies: (PortalChatter.prototype.xmlDependencies || [])
        .concat([
            '/dynco_base/static/src/xml/portal_chatter.xml',
        ]),

    /**
     * @constructor
     */
    init: function (parent, options) {
        this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
    },

});
});
