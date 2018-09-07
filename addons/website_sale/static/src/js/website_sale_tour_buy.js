odoo.define('website_sale.tour', function (require) {
'use strict';

var tour = require("web_tour.tour");
var base = require("web_editor.base");

tour.register('shop_buy_product', {
    test: true,
    url: '/shop',
    wait_for: base.ready()
},
    [
        {
            content: "search conference chair",
            trigger: 'form input[name="search"]',
            run: "text conference chair",
        },
        {
            content: "search conference chair",
            trigger: 'form:has(input[name="search"]) .oe_search_button',
        },
        {
            content: "select conference chair",
            trigger: '.oe_product_cart a:contains("Conference Chair")',
        },
        {
            content: "select Conference Chair Aluminium",
            extra_trigger: '#product_detail',
            trigger: 'label:contains(Aluminium) input',
        },
        {
            content: "select Conference Chair Steel",
            extra_trigger: '#product_detail',
            trigger: 'label:contains(Steel) input',
        },
        {
            content: "click on add to cart",
            extra_trigger: 'label:contains(Steel) input:propChecked',
            trigger: '#product_detail form[action^="/shop/cart/update"] .btn-primary',
        },
        {
            content: "click in modal on 'Proceed to checkout' button",
            trigger: 'button:contains("Proceed to Checkout")',
        },
        {
            content: "add suggested",
            extra_trigger: '#wrap:not(:has(#cart_products:contains("[A8767] Storage Box")))',
            trigger: '.oe_cart:has(tr:contains("Steel")) a:contains("Add to Cart")',
        },
        {
            content: "add one more",
            extra_trigger: '#cart_products tr:contains("Storage Box")',
            trigger: '#cart_products tr:contains("Steel") a.js_add_cart_json:eq(1)',
        },
        {
            content: "remove Headphones",
            extra_trigger: '#cart_products tr:contains("Steel") input.js_quantity:propValue(2)',
            trigger: '#cart_products tr:contains("Storage Box") a.js_add_cart_json:first',
        },
        {
            content: "set one",
            extra_trigger: '#wrap:not(:has(#cart_products tr:contains("Storage Box")))',
            trigger: '#cart_products input.js_quantity',
            run: 'text 1',
        },
        {
            content: "go to checkout",
            extra_trigger: '#cart_products input.js_quantity:propValue(1)',
            trigger: 'a[href*="/shop/checkout"]',
        },
        {
            content: "select payment",
            trigger: '#payment_method label:contains("Wire Transfer")',
        },
        {
            content: "Pay Now",
            //Either there are multiple payment methods, and one is checked, either there is only one, and therefore there are no radio inputs
            extra_trigger: '#payment_method label:contains("Wire Transfer") input:checked,#payment_method:not(:has("input:radio:visible"))',
            trigger: 'button[id="o_payment_form_pay"]:visible:not(:disabled)',
        },
        {
            content: "finish",
            trigger: '.oe_website_sale:contains("Thank you for your order")',
            timeout: 30000,
        }
    ]
);

});
