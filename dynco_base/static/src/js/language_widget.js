/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';

var LanguageDropdown = Widget.extend({
    name: 'language_dropdown',
    template: 'dynco_base.LanguageDropdown',
    events: {
        'click .language_dropdown_item': '_onDropdownItemClick',
        'click .add_language': '_addLanguage'
    },
    init: function () {
        this._super.apply(this, arguments);
    },

    willStart: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            return self.load();
        });
    },

    load: function () {
        var self = this;
        return this._rpc({
            route: '/get_active_language',
        }).then(function (data) {
            self.languagedata = data;
        });
    },

    _onDropdownItemClick: function (ev) {
        var selected_lang = ev.currentTarget.dataset.lang_id
        return this._rpc({
            route: '/set_language',
            params: { lang_id: selected_lang }
        }).then(function (data) {
            self.active_lang = selected_lang

            location.reload()
        });
    },
    _addLanguage: function (ev) {
        this.do_action('base.action_view_base_language_install');
    }
});

SystrayMenu.Items.push(LanguageDropdown);

export default LanguageDropdown;

