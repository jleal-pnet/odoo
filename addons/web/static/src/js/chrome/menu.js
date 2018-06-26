odoo.define('web.Menu', function (require) {
"use strict";

var core = require('web.core');
var dom = require('web.dom');
var session = require('web.session');
var Widget = require('web.Widget');

var Menu = Widget.extend({
    init: function() {
        this._super.apply(this, arguments);
        this.is_bound = $.Deferred();
        this.data = {data:{children:[]}};
        core.bus.on('change_menu_section', this, this.on_change_top_menu);
    },
    start: function() {
        this._super.apply(this, arguments);
        return this.bind_menu();
    },
    do_reload: function() {
        var self = this;
        self.bind_menu();
    },
    bind_menu: function() {
        var self = this;
        this.$secondary_menus = this.$el.parents().find('.o_sub_menu');
        this.$secondary_menus.on('click', 'a[data-menu]', this.on_menu_click);
        this.$el.on('click', 'a[data-menu]', function (event) {
            event.preventDefault();
            var menu_id = $(event.currentTarget).data('menu');
            core.bus.trigger('change_menu_section', {menuID: menu_id});
        });

        // Hide second level submenus
        this.$secondary_menus.find('.oe_menu_toggler').siblings('.oe_secondary_submenu').addClass('o_hidden');
        if (self.current_menu) {
            self.open_menu({id: self.current_menu});
        }
        this.trigger('menu_bound');

        dom.initAutoMoreMenu(this.$el);

        this.is_bound.resolve();
    },
    /**
     * Opens a given menu by id, as if a user had browsed to that menu by hand
     * except does not trigger any event on the way
     *
     * @param {Number} id database id of the terminal menu to select
     */
    open_menu: function (event) {
        var id = event.data.id;
        this.current_menu = id;
        session.active_id = id;
        var $clicked_menu, $sub_menu, $main_menu;
        $clicked_menu = this.$el.add(this.$secondary_menus).find('a[data-menu=' + id + ']');
        this.trigger('open_menu', {id: id, clicked_menu: $clicked_menu});
        if (this.$secondary_menus.has($clicked_menu).length) {
            $sub_menu = $clicked_menu.parents('.oe_secondary_menu');
            $main_menu = this.$el.find('a[data-menu=' + $sub_menu.data('menu-parent') + ']');
        } else {
            $sub_menu = this.$secondary_menus.find('.oe_secondary_menu[data-menu-parent=' + $clicked_menu.attr('data-menu') + ']');
            $main_menu = $clicked_menu;
        }

        this.current_primary_menu = $main_menu.data('menu');

        // Activate current main menu
        this.$el.find('.active').removeClass('active');
        $main_menu.parent().addClass('active');

        // Show current sub menu
        this.$secondary_menus.find('.oe_secondary_menu').hide();
        $sub_menu.show();

        // Hide/Show the leftbar menu depending of the presence of sub-items
        this.$secondary_menus.toggleClass('o_hidden', !$sub_menu.children().length);

        // Activate current menu item and show parents
        this.$secondary_menus.find('.active').removeClass('active');
        if ($main_menu !== $clicked_menu) {
            $clicked_menu.parents().removeClass('o_hidden');
            if ($clicked_menu.is('.oe_menu_toggler')) {
                $clicked_menu.toggleClass('oe_menu_opened').siblings('.oe_secondary_submenu:first').toggleClass('o_hidden');
            } else {
                $clicked_menu.parent().addClass('active');
            }
        }
        // add a tooltip to cropped menu items
        this.$secondary_menus.find('.oe_secondary_submenu li a span').each(function() {
            $(this).tooltip(this.scrollWidth > this.clientWidth ? {title: $(this).text().trim(), placement: 'right'} : 'dispose');
       });
    },
    /**
     * Call open_menu on a menu_item that matches the action_id
     *
     * If `menuID` is a match on this action, open this menu_item.
     * Otherwise open the first menu_item that matches the action_id.
     *
     * @param {Number} id the action_id to match
     * @param {Number} [menuID] a menu ID that may match with provided action
     */
    open_action: function (id, menuID) {
        var $menu = this.$el.add(this.$secondary_menus).find('a[data-action-id="' + id + '"]');
        if (!(menuID && $menu.filter("[data-menu='" + menuID + "']").length)) {
            // menuID doesn't match action, so pick first menu_item
            menuID = $menu.data('menu');
        }
        if (menuID) {
            this.open_menu({id: menuID});
        }
    },
    /**
     * Process a click on a menu item
     *
     * @param {Number} id the menu_id
     */
    menu_click: function(id) {
        if (!id) { return; }

        // find back the menuitem in dom to get the action
        var $item = this.$el.find('a[data-menu=' + id + ']');
        if (!$item.length) {
            $item = this.$secondary_menus.find('a[data-menu=' + id + ']');
        }
        var action_id = $item.data('action-id');
        // If first level menu doesnt have action trigger first leaf
        if (!action_id) {
            if(this.$el.has($item).length) {
                var $sub_menu = this.$secondary_menus.find('.oe_secondary_menu[data-menu-parent=' + id + ']');
                var $items = $sub_menu.find('a[data-action-id]').filter('[data-action-id!=""]');
                if($items.length) {
                    action_id = $items.data('action-id');
                    id = $items.data('menu');
                }
            }
        }
        if (action_id) {
            this.trigger('menu_click', {
                action_id: action_id,
                id: id,
                previous_menu_id: this.current_menu // Here we don't know if action will fail (in which case we have to revert menu)
            }, $item);
        } else {
            console.log('Menu no action found web test 04 will fail');
        }
        this.open_menu({id: id});
    },

    /**
     * Change the current top menu
     *
     * @param {int} [menu_id] the top menu id
     */
    on_change_top_menu: function(event) {
        var self = this;
        this.menu_click(event.data.menuID);
    },
    on_menu_click: function(ev) {
        ev.preventDefault();
        this.menu_click($(ev.currentTarget).data('menu'));
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Returns the id of the current primary (first level) menu.
     *
     * @returns {integer}
     */
    getCurrentPrimaryMenu: function () {
        return this.current_primary_menu;
    },
});

return Menu;
});
