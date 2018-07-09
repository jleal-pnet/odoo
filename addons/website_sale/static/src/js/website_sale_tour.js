odoo.define('website_sale_tour.tour', function (require) {
'use strict';

var tour = require("web_tour.tour");
var base = require("web_editor.base");
var rpc = require("web.rpc");

tour.register('website_sale_tour', {
    test: true,
    url: '/web',
    wait_for: base.ready()
},
    [   {
            content: "Configuration Settings for 'Free Sign Up' and 'Tax-Excluded'",
            trigger: '.o_web_client',
            run: function () {
                var tax_def = rpc.query({
                    model: 'product.product',
                    method: 'set_test_product_tax',
                    args: [],
                });
                var def1 = rpc.query({
                    model: 'res.config.settings',
                    method: 'create',
                    args: [{
                        'auth_signup_uninvited': 'b2c',
                        'sale_show_tax': 'subtotal',
                        'group_show_price_total': false,
                        'group_show_price_subtotal': true,
                    }],
                });
                var def2 = def1.then( function (res_id) {
                    return rpc.query({
                        model: 'res.config.settings',
                        method: 'execute',
                        args: [[res_id]],
                    });
                });
                $.when(tax_def, def2).then(function (res) {
                    window.location.href = '/web/session/logout';
                });
            },
        },
        // Testing b2c with Tax-Excluded Prices
        {
            content: "Click on shop",
            trigger: '#top_menu a[href="/shop"]:visible',
        },
        {
            content: "select Storage Box",
            trigger: '.oe_product_cart a:contains("Storage Box")',
        },
        {
            content: "add one more storage box",
            trigger: '.js_add_cart_json:eq(1)',
        },
        {
            content: "Check b2b Tax-Excluded Prices",
            trigger: '.product_price .oe_currency_value:visible',
            extra_trigger: ".product_price .oe_price .oe_currency_value:containsExact(79.00)",
        },
        {
            content: "click on add to cart",
            trigger: '#add_to_cart',
        },
        {
            content: "Check 2 products in cart",
            extra_trigger: '#cart_products tr:contains("Storage Box") input.js_quantity:propValue(2)',
            trigger: 'a[href*="/shop/checkout"]',
        },
        {
            content: "Check Price b2b subtotal",
            trigger: 'tr#order_total_untaxed .oe_currency_value',
            extra_trigger: "tr#order_total_untaxed .oe_currency_value:containsExact(158.00)",
        },
        {
            content: "Check Price b2b Sale Tax(15%)",
            trigger: 'tr#order_total_taxes .oe_currency_value',
            extra_trigger: "tr#order_total_taxes .oe_currency_value:containsExact(23.70)",
        },
        {
            content: "Check Price b2b Total amount",
            trigger: 'tr#order_total .oe_currency_value',
            extra_trigger: "tr#order_total .oe_currency_value:containsExact(181.70)",
        },
        {
            content: "Writing name in address",
            trigger: 'input[name="name"]',
            run: 'text abc',
        },
        {
            content: "Writing phone number in address",
            trigger: 'input[name="phone"]',
            run: 'text 9999999999',
        },
        {
            content: "Writing email in address",
            trigger: 'input[name="email"]',
            run: 'text abc@odoo.com',
        },
        {
            content: "Writing street and Number in address",
            trigger: 'input[name="street"]',
            run: 'text 1,C.G Road',
        },
        {
            content: "Writing city in address",
            trigger: 'input[name="city"]',
            run: 'text Ahmedabad',
        },
        {
            content: "Select country in address",
            trigger: 'select[name="country_id"]',
            run : function (actions) {
                var country = _.filter($('select[name="country_id"] option'), function (country) {
                    if (country.text === 'India') {
                        return country;
                    }
                });
                actions.text($(country).val());
            }
        },
        {
            content: "Select state in address",
            trigger: 'select[name="state_id"]',
            run : function (actions) {
                actions.text($('select[name="state_id"] option[data-code="GJ"]'));
            }
        },
        {
            content: "Shipping address is not same as billing address",
            trigger: '#shipping_use_same',
        },
        {
            content: "click on next button",
            trigger: '.oe_cart .btn:contains("Next")',
        },
        {
            content: "Writing name in shipping address",
            extra_trigger: 'h2:contains("Shipping Address")',
            trigger: 'input[name="name"]',
            run: 'text def',
        },
        {
            content: "Writing phone number in shipping address",
            trigger: 'input[name="phone"]',
            run: 'text 8888888888',
        },
        {
            content: "Writing street and Number in shipping address",
            trigger: 'input[name="street"]',
            run: 'text 2,xyz',
        },
        {
            content: "Writing city in shipping address",
            trigger: 'input[name="city"]',
            run: 'text baroda',
        },
        {
            content: "Select country in shipping address",
            trigger: 'select[name="country_id"]',
            run : function (actions) {
                var country = _.filter($('option'), function (country) {
                    if (country.text === 'India') {
                        return country;
                    }
                });
                actions.text($(country).val());
            }
        },
        {
            content: "Select state in shipping address",
            trigger: 'select[name="state_id"]',
            run : function (actions) {
                var state = _.filter($('option'), function (state) {
                    if (state.text === 'Gujarat') {
                        return state;
                    }
                });
                actions.text($(state).val());
            }
        },
        {
            content: "click on next button",
            trigger: '.oe_cart .btn:contains("Next")',
        },
        {
            content: "click for edit address",
            trigger: 'a:contains("Edit") i',
        },
        {
            content: "Confirm Address",
            trigger: 'a.btn:contains("Confirm")',
        },
        {
            content: "Select `Wire Transfer` payment method",
            trigger: '#payment_method label:contains("Wire Transfer")',
        },
        {
            content: "Pay Now",
            extra_trigger: '#payment_method label:contains("Wire Transfer") input:checked,#payment_method:not(:has("input:radio:visible"))',
            trigger: 'button[id="o_payment_form_pay"]:visible:not(:disabled)',
        },
        {
            content: "Sign up",
            trigger: '.oe_cart a:contains("Sign Up")',
        },
        {
            content: "Password",
            extra_trigger: '.oe_signup_form .field-login',
            trigger: 'input[name="password"]',
            run: 'text admin',
        },
        {
            content: "Confirm password",
            trigger: 'input[name="confirm_password"]',
            run: 'text admin',
        },
        {
            content: "Click on button sign up",
            trigger: '.oe_signup_form .oe_login_buttons .o_signup_btn',
        },
        {
            content: "See Quotations",
            trigger: '.o_portal_docs a:contains("Quotations")',
        },
        // Sign in as admin change config auth_signup -> b2b, sale_show_tax -> total and Logout
        {
            content: "Open Dropdown for logout",
            trigger: '#top_menu li a.dropdown-toggle:visible span.caret',
        },
        {
            content: "logout",
            trigger: '#o_logout a:contains("Logout")',
        },
        {
            content: "Sign in as admin",
            trigger: '#top_menu li a b:contains("Sign in")',
        },
        {
            content: "Email admin",
            trigger: 'input[name="login"]',
            run: 'text admin',
        },
        {
            content: "Password admin",
            trigger: 'input[name="password"]',
            run: 'text admin',
        },
        {
            content: "Click on Login Button",
            trigger: '.oe_login_buttons .btn.btn-primary:contains("Log in")',
        },
        {
            content: "Configuration Settings for 'Tax Included' and sign up 'On Invitation'",
            trigger: '.o_web_client',
            run: function () {
                var def1 = rpc.query({
                    model: 'res.config.settings',
                    method: 'create',
                    args: [{
                        'auth_signup_uninvited': 'b2b',
                        'sale_show_tax': 'total',
                        'group_show_price_total': true,
                        'group_show_price_subtotal': false,
                    }],
                });
                var def2 = def1.then( function (res_id) {
                    return rpc.query({
                        model: 'res.config.settings',
                        method: 'execute',
                        args: [[res_id]],
                    });
                });
                def2.then(function () {
                    window.location.href = '/web/session/logout';
                });
            },
        },
        // Testing b2b with Tax-Included Prices
        {
            content: "Click on shop",
            trigger: '#top_menu a[href="/shop"]:visible',
        },
        {
            content: "select Storage Box",
            trigger: '.oe_product_cart a:contains("Storage Box")',
        },
        {
            content: "add one more Storage Box",
            trigger: '.js_add_cart_json:eq(1)',
        },
        {
            content: "Check b2c Tax-Excluded Prices",
            trigger: '.product_price .oe_currency_value:visible',
            extra_trigger: ".product_price .oe_price .oe_currency_value:containsExact(90.85)",
        },
        {
            content: "click on add to cart",
            trigger: '#add_to_cart',
        },
        {
            content: "Check 2 products in cart",
            extra_trigger: '#cart_products tr:contains("Storage Box") input.js_quantity:propValue(2)',
            trigger: 'a[href*="/shop/checkout"]',
        },
        {
            content: "Check Price b2c total",
            trigger: 'tr#order_total_untaxed .oe_currency_value',
            extra_trigger: "tr#order_total_untaxed .oe_currency_value:containsExact(158.00)",
        },
        {
            content: "Check Price b2c Sale Tax(15%)",
            trigger: 'tr#order_total_taxes .oe_currency_value',
            extra_trigger: "tr#order_total_taxes .oe_currency_value:containsExact(23.70)",
        },
        {
            content: "Check Price b2c Total amount",
            trigger: 'tr#order_total .oe_currency_value',
            extra_trigger: "tr#order_total .oe_currency_value:containsExact(181.70)",
        },
        {
            content: "Click on Login Button",
            trigger: '.oe_cart a.btn:contains("Log In")',
        },
        {
            content: "Login with account from first record",
            trigger: 'input[name="login"]',
            run: 'text abc@odoo.com'
        },
        {
            content: "Password",
            trigger: 'input[name="password"]',
            run: 'text admin'
        },
        {
            content: "In login button",
            trigger: '.oe_login_buttons .btn.btn-primary:contains("Log in")'
        },
        {
            content: "Add new shipping address",
            trigger: '.one_kanban form[action^="/shop/address"] .btn',
        },
        {
            content: "Writing name in shipping address",
            trigger: 'input[name="name"]',
            run: 'text ghi',
        },
        {
            content: "Writing phone number in shipping address",
            trigger: 'input[name="phone"]',
            run: 'text 7777777777',
        },
        {
            content: "Writing street and Number in shipping address",
            trigger: 'input[name="street"]',
            run: 'text 2,wxy',
        },
        {
            content: "Writing city in shipping address",
            trigger: 'input[name="city"]',
            run: 'text Mumbai',
        },
        {
            content: "Select country in shipping address",
            trigger: 'select[name="country_id"]',
            run : function (actions) {
                var country = _.filter($('option'), function (country) {
                    if (country.text === 'India') {
                        return country;
                    }
                });
                actions.text($(country).val());
            }
        },
        {
            content: "Select state in shipping address",
            trigger: 'select[name="state_id"]',
            run : function (actions) {
                var state = _.filter($('option'), function (state) {
                    if (state.text === 'Gujarat') {
                        return state;
                    }
                });
                actions.text($(state).val());
            }
        },
        {
            content: "click on next button",
            trigger: '.oe_cart .btn:contains("Next")',
        },
        {
            content: "Select `Wire Transfer` payment method",
            trigger: '#payment_method label:contains("Wire Transfer")',
        },
        {
            content: "Pay Now",
            extra_trigger: '#payment_method label:contains("Wire Transfer") input:checked,#payment_method:not(:has("input:radio:visible"))',
            trigger: 'button[id="o_payment_form_pay"]:visible:not(:disabled)',
        },
        {
            content: "Open Dropdown for See quotation",
            extra_trigger: '.thanks_msg',
            trigger: '#top_menu li a.dropdown-toggle:visible span.caret',
        },
        {
            content: "My account",
            extra_trigger: '#top_menu li.dropdown.open:contains("abc")',
            trigger: '.dropdown-menu a[href="/my/home"]:visible',
        },
        {
            content: "See Quotations",
            trigger: '.o_portal_docs a:contains("Quotations")',
        },

        // enable extra step on website congit and check extra step on checkout process
        {
            content: "Open Dropdown for logout",
            trigger: '#top_menu li a.dropdown-toggle:visible span.caret',
        },
        {
            content: "logout",
            trigger: '#o_logout a:contains("Logout")',
        },
        {
            content: "Sign in as admin",
            trigger: '#top_menu li a b:contains("Sign in")',
        },
        {
            content: "Email admin",
            trigger: 'input[name="login"]',
            run: 'text admin',
        },
        {
            content: "Password admin",
            trigger: 'input[name="password"]',
            run: 'text admin',
        },
        {
            content: "Click on Login Button",
            trigger: '.oe_login_buttons .btn.btn-primary:contains("Log in")',
        },
        {
            content: "Enable extra step on checkout process",
            trigger: '.o_web_client',
            run: function () {
                rpc.query({
                    model: 'ir.model.data',
                    method: 'xmlid_to_res_id',
                    args: ['website_sale.extra_info_option'],
                }).then(function (res) {
                    rpc.query({
                        model: 'ir.ui.view',
                        method: 'toggle',
                        args: [[res]],
                    })
                    .then(function (res) {
                        window.location.href = '/web/session/logout';
                    });
                });
            },
        },
        {
            content: "Login with user 'abc'",
            trigger: 'input[name="login"]',
                run: 'text abc@odoo.com',
        },
        {
            content: "Password admin",
            trigger: 'input[name="password"]',
            run: 'text admin',
        },
        {
            content: "Click on Login Button",
            trigger: '.oe_login_buttons .btn.btn-primary:contains("Log in")',
        },
        {
            content: "shop",
            extra_trigger: '#top_menu .dropdown:contains("abc")',
            trigger: '#top_menu a[href="/shop"]:visible',
        },
        {
            content: "select Storage Box",
            trigger: '.oe_product_cart a:contains("Storage Box")',
        },
        {
            content: "click on add to cart",
            trigger: '#add_to_cart',
        },
        {
            content: "Check 2 products in cart",
            extra_trigger: '#cart_products tr:contains("Storage Box")',
            trigger: 'a[href*="/shop/checkout"]',
        },
        {
            content: "check that addres step skipped and click on next button",
            extra_trigger: '.progress-wizard a[href="/shop/checkout"] .progress-wizard-step.complete',
            trigger: 'a[href="/shop/confirm_order"]',
        },
        {
            content: "Check that shipping address is of 2nd order shipping address",
            trigger: '.oe_cart .panel-body div:contains("Shipping") span[itemprop="streetAddress"]:contains("2,wxy, Mumbai , Gujarat GJ, India")',
        },
        {
            content: "Select `Wire Transfer` payment method",
            trigger: '#payment_method label:contains("Wire Transfer")',
        },
        {
            content: "Pay Now",
            extra_trigger: '#payment_method label:contains("Wire Transfer") input:checked,#payment_method:not(:has("input:radio:visible"))',
            trigger: 'button[id="o_payment_form_pay"]:visible',
        },
    ]
);
});
