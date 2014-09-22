define([
    'intern!object',
    'intern/chai!assert',
    'require'
], function(registerSuite, assert, require) {

    registerSuite({

        name: 'home',

        'Basic Test OK': function() {
            assert.ok(true);
        },

        'Ensure homepage is displaying search form': function() {
            console.log(this);

            return this.remote.get('http://developer-local.allizom.org/')
                        .findById('home-q')
                        .click()
                        .type('Hello')
                        .end()
                        .text()
                        .then(function() {
                            assert.ok(resultText == 'Hello')
                        });
        }
    });



});
