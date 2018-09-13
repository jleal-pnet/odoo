odoo.define('web_editor.web_editor_tests', function (require) {
"use strict";

var FormView = require('web.FormView');
var testUtils = require('web.test_utils');
var core = require('web.core');
var FieldHtml = require('web_editor.field.html');
var Wysiwyg = require('web_editor.wysiwyg');
var MediaDialog = require('wysiwyg.widgets.MediaDialog');

var _t = core._t;


QUnit.module('web_editor', {
    beforeEach: function() {
        this.data = {
            'ir.ui.view': {
                fields: {
                    display_name: { string: "Displayed name", type: "char" },
                },
                records: [],
                read_template: function (args) {
                    if (args[0] === 'web_editor.colorpicker') {
                        return '<templates><t t-name="web_editor.colorpicker">' +
                            '<colorpicker>' +
                            '    <div class="o_colorpicker_section" data-name="theme" data-display="Theme Colors" data-icon-class="fa fa-flask">' +
                            '        <button data-color="alpha"></button>' +
                            '        <button data-color="beta"></button>' +
                            '        <button data-color="gamma"></button>' +
                            '        <button data-color="delta"></button>' +
                            '        <button data-color="epsilon"></button>' +
                            '    </div>' +
                            '    <div class="o_colorpicker_section" data-name="transparent_grayscale" data-display="Transparent Colors" data-icon-class="fa fa-eye-slash">' +
                            '        <button class="o_btn_transparent"></button>' +
                            '        <button data-color="black-25"></button>' +
                            '        <button data-color="black-50"></button>' +
                            '        <button data-color="black-75"></button>' +
                            '        <button data-color="white-25"></button>' +
                            '        <button data-color="white-50"></button>' +
                            '        <button data-color="white-75"></button>' +
                            '    </div>' +
                            '    <div class="o_colorpicker_section" data-name="common" data-display="Common Colors" data-icon-class="fa fa-paint-brush"></div>' +
                            '</colorpicker>' +
                        '</t></templates>';
                    }
                },
            },
            'note.note': {
                fields: {
                    display_name: { string: "Displayed name", type: "char" },
                    body: {string: "Message", type: "html"},
                },
                records: [{
                    id: 1,
                    display_name: "first record",
                    body: "<p>toto toto toto</p><p>tata</p>",
                }],
            },
            'mass.mailing': {
                fields: {
                    display_name: { string: "Displayed name", type: "char" },
                    body_html: {string: "Message Body inline (to send)", type: "html"},
                    body_arch: {string: "Message Body for edition", type: "html"},
                },
                records: [{
                    id: 1,
                    display_name: "first record",
                    body_html: "<div class='field_body' style='background-color: red;'>yep</div>",
                    body_arch: "<div class='field_body'>yep</div>",
                }],
            },
        };
    }
});

QUnit.test('field html widget', function (assert) {
    var done = assert.async();
    assert.expect(3);

    testUtils.createAsyncView({
        View: FormView,
        model: 'note.note',
        data: this.data,
        arch: '<form>' +
                '<field name="body" widget="html" style="height: 100px"/>' +
            '</form>',
        res_id: 1,
    }).then(function (form) {
        var $field = form.$('.oe_form_field[name="body"]');
        assert.strictEqual($field.children('.o_readonly').html(),
            '<p>toto toto toto</p><p>tata</p>',
            "should have rendered a div with correct content in readonly");
        assert.strictEqual($field.attr('style'), 'height: 100px',
            "should have applied the style correctly");

        form.$buttons.find('.o_form_button_edit').click();

        $field = form.$('.oe_form_field[name="body"]');
        assert.strictEqual($field.find('.note-editable').html(),
            '<p>toto toto toto</p><p>tata</p>',
            "should have rendered the field correctly in edit");

        form.destroy();
        done();
    });
});

QUnit.test('field html widget: inline-style', function (assert) {
    var done = assert.async();
    assert.expect(2);

    this.data['note.note'].records[0].body = '<p class="pull-right" style="float: right;">toto toto toto</p><p>tata</p>';

    testUtils.createAsyncView({
        View: FormView,
        model: 'note.note',
        data: this.data,
        arch: '<form>' +
                '<field name="body" widget="html" style="height: 100px" options="{\'style-inline\': true}"/>' +
            '</form>',
        res_id: 1,
    }).then(function (form) {
        var $field = form.$('.oe_form_field[name="body"]');

        assert.strictEqual($field.children('.o_readonly').html(), '<p class="pull-right" style="float: right;">toto toto toto</p><p>tata</p>',
            "should have rendered a div with correct content in readonly");

        form.$buttons.find('.o_form_button_edit').click();

        $field = form.$('.oe_form_field[name="body"]');
        assert.strictEqual($field.find('.note-editable').html(), '<p class="pull-right">toto toto toto</p><p>tata</p>',
            "should have rendered the field correctly in edit (remove style inline who used class)");

        form.destroy();
        done();
    });
});

QUnit.test('field html widget: colorpicker', function (assert) {
    var done = assert.async();
    assert.expect(6);

    testUtils.createAsyncView({
        View: FormView,
        model: 'note.note',
        data: this.data,
        arch: '<form>' +
                '<field name="body" widget="html" style="height: 100px"/>' +
            '</form>',
        res_id: 1,
    }).then(function (form) {
        form.$buttons.find('.o_form_button_edit').click();
        var $field = form.$('.oe_form_field[name="body"]');

        // select the text
        var pText = $field.find('.note-editable p').first().contents()[0];
        Wysiwyg.setRange(pText, 1, pText, 10);
        // text is selected

        var range = Wysiwyg.getRange($field[0]);
        assert.strictEqual(range.sc, pText,
            "should select the text");

        $field.find('.note-toolbar .note-bg-color button:first').mousedown().click();

        assert.ok($field.find('.note-bg-color').hasClass('show') && $field.find('.note-bg-color .dropdown-menu').hasClass('show'),
            "should display the color picker");

        $field.find('.note-toolbar .note-bg-color button[data-value="#00FFFF"]').click();

        assert.ok(!$field.find('.note-bg-color').hasClass('show') && !$field.find('.note-bg-color .dropdown-menu').hasClass('show'),
            "should close the color picker");

        assert.strictEqual($field.find('.note-editable').html(),
            '<p>t<font style="background-color: rgb(0, 255, 255);">oto toto&nbsp;</font>toto</p><p>tata</p>',
            "should have rendered the field correctly in edit");

        var fontContent = $field.find('.note-editable font').contents()[0];
        var rangeControl = {
            sc: fontContent,
            so: 0,
            ec: fontContent,
            eo: fontContent.length,
        };
        range = Wysiwyg.getRange($field[0]);
        assert.deepEqual(_.pick(range, 'sc', 'so', 'ec', 'eo'), rangeControl,
            "should select the text after color change");

        // select the text
        pText = $field.find('.note-editable p').first().contents()[2];
        Wysiwyg.setRange(fontContent, 5, pText, 2);
        // text is selected

        $field.find('.note-toolbar .note-bg-color button:first').mousedown().click();
        $field.find('.note-toolbar .note-bg-color button[data-value="bg-gamma"]').click();

        assert.strictEqual($field.find('.note-editable').html(),
            '<p>t<font style="background-color: rgb(0, 255, 255);">oto t</font><font class="bg-gamma">oto&nbsp;to</font>to</p><p>tata</p>',
            "should have rendered the field correctly in edit");

        form.destroy();
        done();
    });
});

QUnit.test('field html widget: media dialog', function (assert) {
    var done = assert.async();
    assert.expect(1);

    testUtils.createAsyncView({
        View: FormView,
        model: 'note.note',
        data: this.data,
        arch: '<form>' +
                '<field name="body" widget="html" style="height: 100px"/>' +
            '</form>',
        res_id: 1,
        mockRPC: function (route, args) {
            if (args.model === 'ir.attachment') {
                if (args.method === "generate_access_token") {
                    return $.when();
                }
                if (args.kwargs.domain[7][2].join(',') === "image/gif,image/jpe,image/jpeg,image/jpg,image/gif,image/png") {
                    return $.when([{
                        "id": 1,
                        "public": true,
                        "name": "image",
                        "datas_fname": "image.png",
                        "mimetype": "image/png",
                        "checksum": false,
                        "url": "/web_editor/static/src/img/transparent.png",
                        "type": "url",
                        "res_id": 0,
                        "res_model": false,
                        "access_token": false
                    }]);
                }
            }
            return this._super(route, args);
        },
    }).then(function (form) {
        form.$buttons.find('.o_form_button_edit').click();
        var $field = form.$('.oe_form_field[name="body"]');

        // the dialog load some xml assets
        var defMediaDialog = $.Deferred();
        testUtils.patch(MediaDialog, {
            init: function () {
                this._super.apply(this, arguments);
                this.opened(defMediaDialog.resolve.bind(defMediaDialog));
            }
        });

        var pText = $field.find('.note-editable p').first().contents()[0];
        Wysiwyg.setRange(pText, 1);

        $field.find('.note-toolbar .note-insert button:has(.note-icon-picture)').mousedown().click();

        // load static xml file (dialog, media dialog, unsplash image widget)
        defMediaDialog.then(function () {
            $('.modal .o_select_media_dialog .o_image:first').click();
            $('.modal .modal-footer button.btn-primary').click();

            var $editable = form.$('.oe_form_field[name="body"] .note-editable');

            assert.strictEqual($editable.html(),
                '<p>t<img class="img-fluid o_we_custom_image" data-src="/web_editor/static/src/img/transparent.png">oto toto toto</p><p>tata</p>',
                "should have the image in the dom");

            testUtils.unpatch(MediaDialog);

            form.destroy();
            done();
        }, 200);
    });
});

QUnit.test('field html translatable', function (assert) {
    assert.expect(3);

    var multiLang = _t.database.multi_lang;
    _t.database.multi_lang = true;

    this.data['note.note'].fields.body.translate = true;

    testUtils.createAsyncView({
        View: FormView,
        model: 'note.note',
        data: this.data,
        arch: '<form string="Partners">' +
                '<field name="body" widget="html"/>' +
            '</form>',
        res_id: 1,
        mockRPC: function (route, args) {
            if (route === '/web/dataset/call_button' && args.method === 'translate_fields') {
                assert.deepEqual(args.args, ['note.note',1,'body',{}], "should call 'call_button' route");
                return $.when();
            }
            return this._super.apply(this, arguments);
        },
    }).then(function (form) {

        assert.strictEqual(form.$('.oe_form_field_html_text .o_field_translate').length, 0,
            "should not have a translate button in readonly mode");

        form.$buttons.find('.o_form_button_edit').click();
        var $button = form.$('.oe_form_field_html_text .o_field_translate');
        assert.strictEqual($button.length, 1, "should have a translate button");
        $button.click();

        form.destroy();
        _t.database.multi_lang = multiLang;

    });
});

});
