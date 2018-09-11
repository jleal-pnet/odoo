odoo.define('mass_mailing.editor', function (require) {
"use strict";

require('web.dom_ready');
var ajax = require('web.ajax');
var core = require('web.core');
var snippets_editor = require('web_editor.snippet.editor');

var $editable_area = $('#editable_area');
var odoo_top = window.top.odoo;

var fn_popover_update = $.summernote.eventHandler.modules.popover.update;
$.summernote.eventHandler.modules.popover.update = function ($popover, oStyle, isAirMode) {
    fn_popover_update.call(this, $popover, oStyle, isAirMode);
    $("span.o_table_handler, div.note-table").remove();
};

ajax.loadXML("/mass_mailing/static/src/xml/mass_mailing.xml", core.qweb);

snippets_editor.Class.include({
    _computeSnippetTemplates: function (html) {
        var self = this;
        var ret = this._super.apply(this, arguments);

        var $themes = this.$("#email_designer_themes").children();
        if ($themes.length === 0) return ret;

        /**
         * Initialize theme parameters.
         */
        var all_classes = "";
        var themes_params = _.map($themes, function (theme) {
            var $theme = $(theme);
            var name = $theme.data("name");
            var classname = "o_" + name + "_theme";
            all_classes += " " + classname;
            var images_info = _.defaults($theme.data("imagesInfo") || {}, {all: {}});
            _.each(images_info, function (info) {
                info = _.defaults(info, images_info.all, {module: "mass_mailing", format: "jpg"});
            });
            return {
                name: name,
                className: classname || "",
                img: $theme.data("img") || "",
                template: $theme.html().trim(),
                nowrap: !!$theme.data('nowrap'),
                get_image_info: function (filename) {
                    if (images_info[filename]) {
                        return images_info[filename];
                    }
                    return images_info.all;
                }
            };
        });
        $themes.parent().remove();

        var $body = $(document.body);
        var $snippets = this.$(".oe_snippet");
        var $snippets_menu = this.$el.find("#snippets_menu");

        /**
         * Create theme selection screen and check if it must be forced opened.
         * Reforce it opened if the last snippet is removed.
         */
        var $dropdown = $(core.qweb.render("mass_mailing.theme_selector", {
            themes: themes_params
        }));
        var first_choice;
        check_if_must_force_theme_choice();

        /**
         * Add proposition to install enterprise themes if not installed.
         */
        var $mail_themes_upgrade = $dropdown.find(".o_mass_mailing_themes_upgrade");
        $mail_themes_upgrade.on("click", function (e) {
            e.stopImmediatePropagation();
            e.preventDefault();
            odoo_top[window.callback+"_do_action"]("mass_mailing.action_mass_mailing_configuration");
        });

        /**
         * Switch theme when a theme button is hovered. Confirm change if the theme button
         * is pressed.
         */
        var selected_theme = false;
        $dropdown.on("mouseenter", ".dropdown-item", function (e) {
            if (first_choice) return;
            e.preventDefault();
            var theme_params = themes_params[$(e.currentTarget).index()];
            switch_theme(theme_params);
        });
        $dropdown.on("click", ".dropdown-item", function (e) {
            e.preventDefault();
            var theme_params = themes_params[$(e.currentTarget).index()];
            if (first_choice) {
                switch_theme(theme_params);
                $body.removeClass("o_force_mail_theme_choice");
                first_choice = false;

                if ($mail_themes_upgrade.length) {
                    $dropdown.remove();
                    $snippets_menu.empty();
                }
            }

            switch_images(theme_params, $snippets);

            selected_theme = theme_params;

            // Notify form view
            odoo_top[window.callback+"_downup"]($editable_area.addClass("o_dirty").html());
        });

        /**
         * If the user opens the theme selection screen, indicates which one is active and
         * saves the information...
         * ... then when the user closes check if the user confirmed its choice and restore
         * previous state if this is not the case.
         */
        $dropdown.on("shown.bs.dropdown", function () {
            check_selected_theme();
            $dropdown.find(".dropdown-item").removeClass("selected").filter(function () {
                return ($(this).has(".o_thumb[style=\""+ "background-image: url(" + (selected_theme && selected_theme.img) + "_small.png)"+ "\"]").length > 0);
            }).addClass("selected");
        });
        $dropdown.on("hidden.bs.dropdown", function () {
            switch_theme(selected_theme);
        });

        /**
         * On page load, check the selected theme and force switching to it (body needs the
         * theme style for its edition toolbar).
         */
        check_selected_theme();
        $body.addClass(selected_theme.className);
        switch_images(selected_theme, $snippets);

        $dropdown.insertAfter($snippets_menu);

        return ret;

        function check_if_must_force_theme_choice() {
            first_choice = editable_area_is_empty();
            $body.toggleClass("o_force_mail_theme_choice", first_choice);
        }

        function editable_area_is_empty($layout) {
            $layout = $layout || $editable_area.find(".o_layout");
            var $mail_wrapper = $layout.children(".o_mail_wrapper");
            var $mail_wrapper_content = $mail_wrapper.find('.o_mail_wrapper_td');
            if (!$mail_wrapper_content.length) { // compatibility
                $mail_wrapper_content = $mail_wrapper;
            }
            return (
                $editable_area.html().trim() === ""
                || ($layout.length > 0 && ($layout.html().trim() === "" || $mail_wrapper_content.length > 0 && $mail_wrapper_content.html().trim() === ""))
            );
        }

        function check_selected_theme() {
            var $layout = $editable_area.find(".o_layout");
            if ($layout.length === 0) {
                selected_theme = false;
            } else {
                _.each(themes_params, function (theme_params) {
                    if ($layout.hasClass(theme_params.className)) {
                        selected_theme = theme_params;
                    }
                });
            }
        }

        function switch_images(theme_params, $container) {
            if (!theme_params) return;
            $container.find("img").each(function () {
                var $img = $(this);
                var src = $img.attr("src");

                var m = src.match(/^\/web\/image\/\w+\.s_default_image_(?:theme_[a-z]+_)?(.+)$/);
                if (!m) {
                    m = src.match(/^\/\w+\/static\/src\/img\/(?:theme_[a-z]+\/)?s_default_image_(.+)\.[a-z]+$/);
                }
                if (!m) return;

                var file = m[1];
                var img_info = theme_params.get_image_info(file);

                if (img_info.format) {
                    src = "/" + img_info.module + "/static/src/img/theme_" + theme_params.name + "/s_default_image_" + file + "." + img_info.format;
                } else {
                    src = "/web/image/" + img_info.module + ".s_default_image_theme_" + theme_params.name + "_" + file;
                }

                $img.attr("src", src);
            });
        }

        function switch_theme(theme_params) {
            if (!theme_params || switch_theme.last === theme_params) return;
            switch_theme.last = theme_params;

            $body.removeClass(all_classes).addClass(theme_params.className);

            var $old_layout = $editable_area.find('.o_layout');

            var $new_wrapper;
            var $new_wrapper_content;
            if (theme_params.nowrap) {
                $new_wrapper = $('<div/>', {class: 'oe_structure'});
                $new_wrapper_content = $new_wrapper;
            } else {
                // This wrapper structure is the only way to have a responsive
                // and centered fixed-width content column on all mail clients
                $new_wrapper = $('<table/>', {class: 'o_mail_wrapper'});
                $new_wrapper_content = $('<td/>', {class: 'o_mail_no_options o_mail_wrapper_td oe_structure'});
                $new_wrapper.append($('<tr/>').append(
                    $('<td/>', {class: 'o_mail_no_resize o_not_editable', contenteditable: 'false'}),
                    $new_wrapper_content,
                    $('<td/>', {class: 'o_mail_no_resize o_not_editable', contenteditable: 'false'})
                ));
            }
            var $new_layout = $('<div/>', {class: 'o_layout ' + theme_params.className}).append($new_wrapper);

            var $contents;
            if (first_choice) {
                $contents = theme_params.template;
            } else if ($old_layout.length) {
                $contents = ($old_layout.hasClass('oe_structure') ? $old_layout : $old_layout.find('.oe_structure').first()).contents();
            } else {
                $contents = $editable_area.contents();
            }

            $new_wrapper_content.append($contents);
            switch_images(theme_params, $new_wrapper_content);
            $editable_area.empty().append($new_layout);
            $old_layout.remove();

            if (first_choice) {
                self._registerDefaultTexts($new_wrapper_content);
                if(theme_params.name == 'basic') {
                    $editable_area.focusIn();
                }
            }
            self._disableUndroppableSnippets();
        }
    },
    cleanForSave: function () {
        this._super.apply(this, arguments);
        // remove font-family from all elements for plain text theme (just like gmail)
        var $basicTheme = this.$editable.find('.o_basic_theme');
        if($basicTheme.length && this.$editable.data('oe-model') === 'mail.mass_mailing') {
            this.$editable.find('*').css('font-family', '');
        }
    }
});

});
