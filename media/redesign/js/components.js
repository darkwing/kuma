(function(doc, $) {
    'use strict';

    var focusClass = 'focused';
    var noop = function(){};

    /*
        Plugin to create nav menus, show/hide delays, etc.
        Accessible by keyboard too!
    */
    $.fn.mozMenu = function(options) {

        var settings = $.extend({
            showDelay: 100,
            hideDelay: 100,
            submenu: null,
            focusOnOpen: false,
            brickOnClick: false,
            onOpen: noop,
            onClose: noop
        }, options);

        var closeTimeout;
        var showTimeout;

        return $(this).each(function() {
            var $self = $(this);
            var $li = $self.parent();
            var initialized;

            // Brick on click?
            var brick = settings.brickOnClick;
            if(brick) {
                $self.on('click', function(e) {
                    if(typeof brick != 'function' || brick(e)) e.preventDefault();
                });
            }

            // Find a submenu.    If one doesn't exist, no need to go further
            var $submenu = (settings.submenu || $li.find('.submenu'));

            // Add a mouseenter / focus event to get the showing of the submenu in motion
            $self.on('mouseenter focus', function() {

                // If this is a fake focus set by us, ignore this
                if($submenu.ignoreFocus) return;

                // If no submenu, go
                if(!$submenu.length) {
                    clear(showTimeout);
                    $.fn.mozMenu.$openMenu && closeSubmenu(getOpenParent());
                    return;
                }

                // Lazy-initialize events that aren't needed until an item is entered.
                if(!initialized) {
                    initialized = 1;

                    // Add the close
                    var $closeButton = $('<button class="submenu-close transparent">\
                        <span class="offscreen">' + gettext('Close submenu') + '</span>\
                        <i aria-hidden="true" class="icon-remove-sign"></i>\
                    </button>').appendTo($submenu);

                    // Hide the submenu when the main menu is blurred for hideDelay
                    $self.on('mouseleave focusout', function() {
                        clear(showTimeout);
                        closeSubmenu($submenu);
                    });

                    // Hide the submenu when the submenu is blurred for hideDelay
                    $submenu.on('mouseleave', function() {
                        clear(showTimeout);
                        closeSubmenu($submenu);
                    });

                    // Cancel the close timeout if moving from main menu item to submenu
                    $submenu.on('mouseenter focusin', function() {
                        clear(closeTimeout);
                    });

                    // Close if it's the last link and they press tab *or* the hit escape
                    $submenu.on('keyup', function(e) {
                        if(e.keyCode == 27) { // Escape
                            closeSubmenu($submenu);
                            $submenu.ignoreFocus = true;
                            setTimeout(function() { $submenu.ignoreFocus = false; }, 10);
                            $self[0].focus();
                        }
                    });

                    $closeButton.on('click', function(){
                        closeSubmenu($(this).parent());
                    });
                }
                // If there's an open submenu and it's not this one, close it
                // Used for tab navigation from submenu to the next menu item
                if($.fn.mozMenu.$openMenu && $.fn.mozMenu.$openMenu != $self) {
                    clear(showTimeout);
                    closeSubmenu(getOpenParent());
                }
                else if($.fn.mozMenu.$openMenu == $self) {
                    clear(closeTimeout);
                }

                // Keep the open menu on this fn itself so only one menu can be open at any time,
                // regardless of the instance or menu group
                $.fn.mozMenu.$openMenu = $self;

                // Show my submenu after the showDelay
                showTimeout = setTimeout(function() {
                    // Setting z-index here so that current menu is always on top
                    $submenu.css('z-index', 99999).addClass('open').attr('aria-hidden', 'false').fadeIn();

                    // Find the first link for improved usability
                    if(settings.focusOnOpen) {
                        var firstLink = $submenu.find('a').get(0);
                        if(firstLink) {
                            try { // Putting in try/catch because of opacity/focus issues in IE
                                $(firstLink).addClass(focusClass) && firstLink.focus();
                            }
                            catch(e){
                                console.log('Exception! ', e);
                            }
                        }
                    }
                    settings.onOpen();
                }, settings.showDelay);
            });
        });

        // Gets the open parent
        function getOpenParent() {
            return $.fn.mozMenu.$openMenu.parent().find('.submenu');
        }

        // Clears the current timeout, interrupting fade-ins and outs as necessary
        function clear(timeout) {
            timeout && clearTimeout(timeout);
        }

        // Closes a given submenu
        function closeSubmenu($sub) {
            closeTimeout = setTimeout(function() {
                // Set the z-index to one less so another menu would get top spot if overlapping and opening
                $sub && $sub.css('z-index', 99998).removeClass('open').attr('aria-hidden', 'true').fadeOut();
                settings.onClose();
            }, settings.hideDelay);
        }
    };

    /*
        Plugin to listen for special keyboard keys and will fire actions based on them
    */
    $.fn.mozKeyboardNav = function(options) {
        var settings = $.extend({
            itemSelector: 'a',
            onEnterKey: noop,
            alwaysCollectItems: false
        }, options);

        var $selectedItem;

        return $(this).each(function() {

            var $items = $(this).find(settings.itemSelector);

            if(!$items.length) return;

            var $self = $(this);

            $self.on('keydown', function(e) {
                var code = e.keyCode;
                var charCode = e.charCode;
                var numberKeyStart = 49;

                // If we should always get fresh items, do so
                if(settings.alwaysCollectItems) {
                    $items = $(this).find(settings.itemSelector);
                    $selectedItem = null;
                }

                // Up and down buttons
                if(code == 38 || code == 40) {
                    e.preventDefault();
                    e.stopPropagation();

                    // Find currently selected item and clear
                    $selectedItem = $items.filter('.' + focusClass).removeClass(focusClass);

                    // Tricky...if they clicked elsewhere in the mean time, we may need to try to
                    // figure it out by activeElement
                    var index = $items.index($selectedItem);
                    var activeElementIndex = doc.activeElement && $items.index(doc.activeElement);
                    if(activeElementIndex > -1) {
                        index = activeElementIndex;
                    }
                    if(index < 0) {
                        index = 0;
                    }

                    // If nothing is currently selected, start with first no matter which key
                    var $next = $($items.get(index + 1));
                    var $prev = $($items.get(index - 1));

                    if(code == 38) {    // up
                        $prev.length && selectItem($prev);
                    }
                    else if(code == 40) {    // down
                        selectItem($next.length ? $next : $items.first());
                    }
                }
                // Number keys: 1, 2, 3, etc.
                else if(charCode >= numberKeyStart && charCode <= 57) {
                    var item = $items.get(charCode - numberKeyStart);
                    item && selectItem(item);
                }
                // Enter key
                else if(code == 13) {
                    settings.onEnterKey($selectedItem);
                }
            });

        });

        function selectItem(item) {
            $(item).addClass(focusClass).get(0).focus();
            $selectedItem = item;
        }

    };

    /*
        Plugin to listen for special keyboard keys and will fire actions based on them
    */
    $.fn.mozTogglers = function(options) {
        var settings = $.extend({
            onOpen: noop,
            slideCallback: noop,
            duration: 200 /* 400 is the default for jQuery */
        }, options);

        $(this).each(function() {
            var $self = $(this);
            var pieces = getTogglerComponents($self);
            var closedAttribute = 'data-closed';

            // Initialize open / close for the purpose of animation
            if($self.hasClass('closed')) {
                $self.attr(closedAttribute, 'true').removeClass('closed');
                pieces.$container.hide();
            }
            setIcon(pieces.$toggler, $self);

            // Add aria to indicate dropdown menu
            pieces.$toggler.attr('aria-haspopup', true);

            // Close on ESC
            $self.on('keyup', '.toggle-container', function(e) {
                e.preventDefault();
                e.stopPropagation();
                if(e.keyCode == 27) {
                    $(this).siblings('a').trigger('mdn:click').focus();
                };
            });

            // Click event to show/hide
            $self.on('click mdn:click', '.toggler', function(e) {
                e.preventDefault();
                e.stopPropagation();
                settings.onOpen.call(this);

                // If I'm an accordion, close the other one
                var $parent = $self.closest('ol, ul');
                if($parent.hasClass('accordion')) {
                    var $current = $parent.find('> .current');
                    if($current.length && $current.get(0) != $self.get(0)) {
                        toggle($current, true);
                    }
                }

                // Open or close the item, set the icon, etc.
                toggle($self);
            });

            // The toggler can be initially opened via a data- attribute
            if($self.attr('data-default-state') == 'open') {
                toggle($self);
            }

            function toggle($li, forceClose) {
                var pieces = getTogglerComponents($li);

                if(!getState($li) || forceClose) {
                    $li.attr(closedAttribute, 'true').removeClass('current');
                    pieces.$container.attr('aria-expanded', false);
                    pieces.$container.slideUp(settings.duration, settings.slideCallback);
                }
                else {
                    $li.attr(closedAttribute, '').addClass('current');
                    pieces.$container.attr('aria-expanded', true);
                    pieces.$container.slideDown(settings.duration, settings.slideCallback);
                }
                setIcon(pieces.$toggler, $li);
            }

            function getTogglerComponents($li) {
                return {
                    $container: $li.find('> .toggle-container'),
                    $toggler: $li.find('> .toggler')
                };
            }

            function setIcon($tog, $li) {
                var openIcon = $tog.attr('data-open-icon') || 'icon-caret-right';
                var closedIcon = $tog.attr('data-closed-icon') || 'icon-caret-down';
                $tog.find('i').attr('class', (getState($li) ? openIcon : closedIcon));
            }

            function getState($li) {
                return $li.attr(closedAttribute);
            }
        });
    };

    /*
        Plugin to adds a native html5 contextmenu
        Callback passes two arguments, event.target and the menu-element
    */
    $.fn.mozContextMenu = function(callback) {
        return $(this).on('contextmenu', function(e) {
            callback(e.target, $('#' + $(this).attr('contextmenu')));
        });
    };

    /*
        Plugin to lazyload images
    */
    $.fn.mozLazyloadImage = function() {
        return $(this).each(function() {
            var $img = $('<img />');
            var alt = $(this).data('alt');
            $img.on('load', function() {
                $(this)
                    .attr('alt', alt)
                    .addClass('loaded');
            });
            $.each($(this).data(), function(name, value) {
                if (name !== "alt") {
                    $img.attr(name, value);
                }
            });
            $(this).after($img).remove();
        });
    };

})(document, jQuery);
