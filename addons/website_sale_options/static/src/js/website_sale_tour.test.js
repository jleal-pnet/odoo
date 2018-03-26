odoo.define('website_sale_tour.test', function (require) {
'use strict';

var tour = require("web_tour.tour");

var steps = tour.tours.website_sale_tour.steps;
for (var k=0; k<steps.length; k++) {
    if (steps[k].content === "click on add to cart") {
        steps.splice(k+1, 0, {
            content: "click in modal on 'Proceed to checkout' button",
            trigger: 'a:contains("Proceed to Checkout")',
        });
    }
}

});
