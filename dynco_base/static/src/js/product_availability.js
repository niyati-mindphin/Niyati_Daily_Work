odoo.define("dynco_base.load", function (require) {
    "use strict";
    var ajax = require("web.ajax");
    var core = require("web.core");
    var QWeb = core.qweb;
    var load_xml = ajax.loadXML(
        "/dynco_base/static/src/xml/product_availability.xml",
        QWeb
    );
});