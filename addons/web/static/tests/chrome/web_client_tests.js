odoo.define('web.web_client_tests', function (require) {
"use strict";

var mailTestUtils = require('mail.testUtils');

var core = require('web.core');
var session = require('web.session');
var SystrayMenu = require('web.SystrayMenu');
var testUtils = require('web.test_utils');
var WebClient = require('web.WebClient');
var Widget = require('web.Widget');

var WEBCLIENT_HTML =
    '<div class="o_web_client">' +
        '<ul class="nav navbar-nav navbar-left oe_application_menu_placeholder" style="display: none;">' +
            '<li>' +
                '<a href="/web?&amp;#menu_id=75&amp;action=88" class="oe_menu_leaf" data-menu="75" data-action-id="88">' +
                    'Some Action' +
                '</a>' +
            '</li>' +
            '<li>' +
                '<a href="/web?&amp;#menu_id=75&amp;action=13" class="oe_menu_leaf" data-menu="78"data-action-id="18">' +
                    'Other Action' +
                '</a>' +
            '</li>' +
        '</ul>' +
        '<div class="o_main_content"/>' +
    '</div>';

function createWebClient(params) {
    params = params || {};
    var $target = $('#qunit-fixture');
    if (params.debug) {
        $target = $('body');
    }

    var $webClient = $(WEBCLIENT_HTML);
    $target.append($webClient);

    var webClient = new WebClient();

    // when 'document' addon is installed, the sidebar does a 'search_read' on
    // model 'ir_attachment' each time a record is open, so we monkey-patch
    // 'mockRPC' to mute those RPCs, so that the tests can be written uniformly,
    // whether or not 'document' is installed
    var mockRPC = params.mockRPC;
    _.extend(params, {
        mockRPC: function (route, args) {
            if (args.model === 'ir.attachment') {
                return $.when([]);
            }
            if (mockRPC) {
                return mockRPC.apply(this, arguments);
            }
            return this._super.apply(this, arguments);
        },
    });
    testUtils.addMockEnvironment(webClient, _.defaults(params, {debounce: false}));

    webClient.setElement($webClient);
    webClient.start();
    return webClient;
}


QUnit.module('Web Client', {
    beforeEach: function () {
        this.data = {
            'res.users': {
                fields: {
                    action_id: {string: "Action ID", type: "integer"},
                },
                records: [
                    {id: 42, action_id: false}
                ],
            },
            partner: {
                fields: {
                    foo: {string: "Foo", type: "char"},
                },
                records: [
                    {id: 1, foo: "yop"},
                ],
            },
        };

        this.actions = [{
            id: 88,
            name: 'A Client Action',
            tag: 'initialAction',
            type: 'ir.actions.client',
        }, {
            id: 3,
            name: 'Partners',
            res_model: 'partner',
            type: 'ir.actions.act_window',
            views: [[false, 'list'], [false, 'form']],
        }];

        this.archs = {
            // list views
            'partner,false,list': '<tree><field name="foo"/></tree>',

            // form views
            'partner,false,form': '<form>' +
                    '<field name="display_name"/>' +
                    '<field name="foo"/>' +
            '</form>',

            // search views
            'partner,false,search': '<search><field name="foo" string="Foo"/></search>',
        };

        var ClientAction = Widget.extend({
            className: 'o_client_action_test',
            start: function () {
                this.$el.text('Hello Old Friend');
            },
        });
        core.action_registry.add('initialAction', ClientAction);

        // we need to patch a few things in the session to make these tests
        // work without talking to a real server.
        testUtils.patch(session, {
            session_is_valid: _.constant(true),
            uid: 42,
        });

        // some addons adds stuff in the systray, such as the messaging system.
        // this adds some noise and makes the tests more difficult to write, so
        // we disable them for the duration of each test.
        this.initialSystrayMenuItems = SystrayMenu.Items;
        SystrayMenu.Items = [];

        // hash can be changed by web client, so it needs to be saved/restored
        this.initialHash = window.location.hash;
        window.location.hash = '';
    },
    afterEach: function () {
        testUtils.unpatch(session);
        SystrayMenu.Items = this.initialSystrayMenuItems;
        delete core.action_registry.map.initialAction;
        window.location.hash = this.initialHash;
    },
}, function () {

    QUnit.test('simple rendering', function (assert) {
        assert.expect(4);

        var webClient = createWebClient({
            data: this.data,
            actions: this.actions,
            services: [mailTestUtils.createBusService()],
            mockRPC: function (route) {
                assert.step(route);
                return this._super.apply(this, arguments);
            },
        });
        assert.verifySteps([
            "/web/dataset/call_kw/res.users/read", // read default user actionID
            "/web/action/load",                    // load initial action data
        ]);
        assert.strictEqual(webClient.$('.o_client_action_test').text(), 'Hello Old Friend',
            "should have rendered the client action");
        webClient.destroy();
    });

    QUnit.test('hash change will load corresponding action', function (assert) {
        assert.expect(7);
        var done = assert.async();

        var webClient = createWebClient({
            data: this.data,
            actions: this.actions,
            services: [mailTestUtils.createBusService()],
            archs: this.archs,
            mockRPC: function (route) {
                assert.step(route);
                return this._super.apply(this, arguments);
            },
        });

        $(window).one('hashchange', function () {
            assert.verifySteps([
                "/web/dataset/call_kw/res.users/read", // read default user actionID
                "/web/action/load",                    // load initial action data
                "/web/action/load",                    // load action 3
                "/web/dataset/call_kw/partner",        // load views for partner
                "/web/dataset/search_read",            // read records for list view
            ]);
            assert.ok(webClient.$('.o_list_view').length,
                "should have a list view in dom");
            webClient.destroy();
            done();
        });
        window.location.hash = 'action=3';
    });

    QUnit.test('hash change will load corresponding action', function (assert) {
        // with this test, we simulate the fact that the web client could take
        // some time to load data and do its initial action, and meanwhile, the
        // user could have done another action.  In that case, the user action
        // should have priority, since its intent was given last.
        assert.expect(1);
        var done = assert.async();

        var loadInitialActionDef = $.Deferred();
        var webClient = createWebClient({
            data: this.data,
            services: [mailTestUtils.createBusService()],
            actions: this.actions,
            archs: this.archs,
            mockRPC: function (route, args) {
                var result = this._super.apply(this, arguments);
                if (route === '/web/action/load' && args.kwargs.action_id === 88) {
                    return loadInitialActionDef.then(_.constant(result));
                }
                return result;
            },
        });

        $(window).one('hashchange', function () {
            loadInitialActionDef.resolve();
            assert.ok(webClient.$('.o_list_view').length,
                "should have a list view in dom");
            webClient.destroy();
            done();
        });

        window.location.hash = 'action=3';
    });
});

});
