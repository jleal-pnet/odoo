odoo.define('payment_stripe.stripe', function(require) {
    "use strict";

    var ajax = require('web.ajax');
    var Dialog = require('web.Dialog');

    require('web.dom_ready');
    if (!$('.o_payment_form').length) {
        return $.Deferred().reject("DOM doesn't contain '.o_payment_form'");
    }

    var observer = new MutationObserver(function(mutations, observer) {
        for(var i=0; i<mutations.length; ++i) {
            for(var j=0; j<mutations[i].addedNodes.length; ++j) {
                if(mutations[i].addedNodes[j].tagName.toLowerCase() === "form" && mutations[i].addedNodes[j].getAttribute('provider') == 'stripe') {
                    do_stripe_payment($(mutations[i].addedNodes[j]));
                }
            }
        }
    });

    function dispay_error (message, acquirer_id) {
        $('#payment_error').remove();
        var $acquirerForm = $('#o_payment_form_acq_' + acquirer_id);
        var messageResult = '<div class="alert alert-danger mb4" id="payment_error">';
        messageResult = messageResult + _.str.escapeHTML(message) + '</div>';
        $acquirerForm.append(messageResult);
        $(".stripe_container").remove();
        $("#o_payment_form_pay").removeAttr('disabled');
    }

    function stripe_none_flow_payment (data, acquirer_id) {
        if (data) {
            $("#o_payment_form_pay").attr('disabled', 'disabled');
            ajax.jsonRpc('/stripe/payment/noneflow/', 'call', data).done(function (result) {
                window.location.href = result;
            }).fail(function(message, data) {
                dispay_error(message.data.message, acquirer_id);
            });
        }
    }

    function input_validation (payment_type, acquirer_id) {
        var $form = $('#o_payment_type_' + payment_type + "_" + acquirer_id);
        var res = true
        $($form.find('input[data-is-required="true"]')).filter(function () {
            if($.trim($(this).val()).length == 0) {
                dispay_error("Please fill all the details correctly", acquirer_id);
                res = false;
            }
        });
        return res;
    }

    function do_stripe_payment (provider_form) {
        // Open Checkout with further options
        var payment_form = $('.o_payment_form');
        var $loader = '<div class="stripe_container text-center text-muted">'+'<i class="fa fa-circle-o-notch fa-4x fa-spin"></i>'+
                        '</div>';
        $(payment_form).append($loader);
        if(!payment_form.find('i').length)
            payment_form.append('<i class="fa fa-spinner fa-spin"/>');
            payment_form.attr('disabled','disabled');

        var get_input_value = function(name) {
            return provider_form.find('input[name="' + name + '"]').val();
        }

        var get_payment_value = function(name) {
            return payment_form.find('input[name="' + name + '"]').val();
        }

        var payment_tx_url = get_payment_value('prepare_tx_url');
        var access_token = get_payment_value('access_token') || get_payment_value('token') || '';
        var acquirer_id = parseInt(get_input_value('acquirer'));
        var amount = parseFloat(get_input_value("amount") || '0.0');
        var currency = get_input_value("currency");
        var email = get_input_value("email");

        $('#payment_error').remove();
        var $select = payment_form.find('.stripe_payment_type');
        var type = $select.val().toLowerCase().replace(/\ /g, '_');
        if (type == 'select_payment_type') {
            dispay_error('Please select any Payment method.', acquirer_id)
            return;
        }
        var stripe = Stripe(get_input_value('stripe_key'));
        var data = {
            'type': type,
            'owner[name]': get_input_value('name'),
            'owner[email]': email,
            'redirect[return_url]': get_input_value('redirect_url'),
            'amount': amount * 100,
            'currency': currency,
            'metadata[return_url]': get_input_value('return_url'),
            'metadata[reference]': get_input_value('reference'),
            'owner[address][city]': get_input_value('city'),
            'owner[address][line1]': get_input_value('line1'),
            'owner[address][state]': get_input_value('state'),
            'owner[address][country]': get_input_value('country'),
            'owner[address][postal_code]': get_input_value('postal_code'),
        }
        if (type == 'card') {
            if (!input_validation('card', acquirer_id)) {return;}
            data = _.extend({}, data, {
                'card[number]': get_payment_value('cc_number').replace(/\ /g, ''),
                'card[exp_month]': get_payment_value('cc_expiry').slice(0,2),
                'card[exp_year]': get_payment_value('cc_expiry').slice(-2),
                'card[cvc]': get_payment_value('cvc'),
                'acquirer_id': acquirer_id
            });
            return stripe_none_flow_payment(data, acquirer_id)
        } else if (type == 'sofort') {
            data = _.extend({}, data, {
                'sofort[country]': get_input_value('country')
            });
        } else if (type == 'sepa_debit') {
            if (!input_validation('sepa_debit', acquirer_id)) {return;}
            data = _.extend({}, data, {
                'sepa_debit[iban]': get_payment_value('iban_number'),
                'acquirer_id': acquirer_id
            });
            return stripe_none_flow_payment(data, acquirer_id);
        }
        stripe.createSource(data).then(function (result) {
            if (result.error) {
                dispay_error(result.error.message, acquirer_id);
            } else {
                $("#o_payment_form_pay").attr('disabled', 'disabled');
                if (result.source.flow === 'redirect' || result.source.type === 'multibanco') {
                    window.location.href = result.source.redirect.url;
                }
                else if (result.source.type == 'wechat') {
                    var $qrcode = $(".o_stripe_wechat");
                    $qrcode.qrcode({
                        width: 128,
                        height: 128,
                        style: "display= block",
                        text: result.source.wechat.qr_code_url
                    });
                    $qrcode.children().css({display: 'block', margin:'auto'});
                    $(".stripe_container").remove();
                }
            }
        });
    }
    $.getScript("/payment_stripe/static/src/lib/jquery.qrcode.min.js");
    $.getScript("https://js.stripe.com/v3/", function(data, textStatus, jqxhr) {
        observer.observe(document.body, {childList: true});
        do_stripe_payment($('form[provider="stripe"]'));
    });
});
