odoo.define("website_sale.tour_shop", function (require) {
    "use strict";

    var tour = require("web_tour.tour");
    var base = require("web_editor.base");

    tour.register("shop_custom_attribute_value", {
        url: "/shop",
        test: true,
        wait_for: base.ready()
    }, [{
        trigger: 'img[src*="/product.template/9"]',
        run: 'click'
    }, {
        trigger: 'li.js_attribute_value span:contains(Custom)',
        extra_trigger: 'li.js_attribute_value',
        run: 'click',
    }, {
        trigger: 'input.variant_custom_value',
        run: 'text Wood',
    }, {
        trigger: 'a:contains(Add to Cart)',
        run: 'click',
    }, {
        trigger: 'div:contains(Custom: Wood)',
        extra_trigger: '.js_product.in_cart.main_product',
        run: function (){} // checks that Yep, it's wood!
    }, {
        trigger: 'button:has(span:contains(Proceed to Checkout))',
        run: 'click',
    }, {
        trigger: 'span:contains(Custom: Wood)',
        extra_trigger: '#cart_products',
        run: function (){}, // check
    }]);
});
