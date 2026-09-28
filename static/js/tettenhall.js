/*
 * Everything the pages need from JavaScript: the CSRF header htmx has to send, the toasts, the
 * account menu in the navbar, and the row menus on the roster. A static file rather than a block in "base.html", so nothing here is
 * rendered by Django and no value has to survive being written into a script literal.
 */
(() => {
    'use strict';

    // Travels as an attribute on "body" for the same reason this file is static at all.
    const CSRF_TOKEN = document.body.dataset.csrfToken;

    document.body.addEventListener('htmx:configRequest', (event) => {
        event.detail.headers['X-CSRFToken'] = CSRF_TOKEN;
    });

    /*
     * A second is not long enough to read a sentence like "This game is over. Start a new savegame to
     * play on.", and for several actions the toast is the only feedback there is.
     */
    const TOAST_TIMEOUT = 5000;

    /*
     * Every toast sits at the bottom, because the navbar is the first thing in the body and has no
     * offset under it: a top-centre notification covers the nav links and the resource counters, and
     * the counters are what several of these toasts are reporting a change to.
     *
     * Below "md:" it clears the furniture that is pinned down there - the section nav on most screens,
     * the fight's docked Fight! button on one - by the same 24 that "base.html" reserves as bottom
     * padding for it. A toast outranks all of it on z-index, so without the offset it covers a control
     * for its full timeout, and on the fight screen the control it covers is the one the screen exists
     * for, at the moment an error toast is the reason the player wants it.
     */
    const HOST_CLASS = 'fixed bottom-24 left-1/2 z-50 flex w-full max-w-md -translate-x-1/2 flex-col items-center gap-y-2 px-4 md:bottom-4';
    const TOAST_CLASS = 'w-full border bg-raised px-4 py-3 text-sm text-ink';

    /*
     * Django's level tags, plus the "success" and "error" this file raises itself.
     *
     * The level is carried by the rule around the toast and by the word above the message, not by a
     * colour behind it: the palette keeps one red and spends it on things that went wrong, so a toast
     * saying a warrior was hired cannot be a different hue from one saying he could not be. Two
     * outlines, and the label says which of the five it actually is.
     */
    const LEVEL_CLASS = {
        debug: 'border-rule',
        info: 'border-rule',
        success: 'border-rule',
        warning: 'border-blood',
        error: 'border-blood',
    };

    const LABEL_CLASS = 'mb-1 font-mono text-label uppercase tracking-label text-ink-muted';

    let host = null;

    const toastHost = () => {
        if (!host) {
            host = document.createElement('div');
            host.className = HOST_CLASS;
            document.body.appendChild(host);
        }
        return host;
    };

    const toast = (text, level) => {
        if (!text) {
            return;
        }
        const element = document.createElement('div');
        element.className = `${TOAST_CLASS} ${LEVEL_CLASS[level] || LEVEL_CLASS.info}`;
        // The level, said in words, because the outline only separates trouble from the rest.
        const label = document.createElement('div');
        label.className = LABEL_CLASS;
        label.textContent = LEVEL_CLASS[level] ? level : 'info';
        element.appendChild(label);
        // "textContent", never "innerHTML": the text arrives from a faction or town name the player
        // typed, and this is the sink that decides whether that is markup or words. The message goes
        // in a child of its own so the label above it is not part of the same text node.
        const body = document.createElement('div');
        body.textContent = text;
        element.appendChild(body);
        // A warning or an error interrupts; the rest is progress the player does not have to be
        // pulled away from.
        element.setAttribute('role', level === 'error' || level === 'warning' ? 'alert' : 'status');
        toastHost().appendChild(element);
        window.setTimeout(() => element.remove(), TOAST_TIMEOUT);
    };

    document.body.addEventListener('notification', (event) => toast(event.detail.value, 'success'));

    document.body.addEventListener('htmx:beforeOnLoad', (event) => {
        const status = event.detail.xhr.status;
        if (500 <= status && status < 600) {
            toast('An error has occurred.', 'error');
        }
    });

    // The server-rendered ones. Trimmed because the formatter is free to put the value on its own line.
    document.querySelectorAll('template[data-toast]').forEach((element) => {
        toast(element.content.textContent.trim(), element.dataset.level);
    });

    const openMenus = () => document.querySelectorAll('details[data-menu][open]');

    // The two things "details" does not give: Escape closes it, and so does a click somewhere else on
    // the page. Whichever menu is open is the thing covering the page.
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            openMenus().forEach((element) => {
                element.open = false;
            });
        }
    });

    document.addEventListener('click', (event) => {
        openMenus().forEach((element) => {
            if (!element.contains(event.target)) {
                element.open = false;
            }
        });
    });

    /*
     * The row menu - see "faction/warrior/components/roster_row_menu.html". The browser opens and
     * closes it; this places it and runs its two steps.
     *
     * Placed beside its trigger, to the left, tops aligned - not under it, where it would cover the
     * next row's trigger and turn "open the next man's menu" into a click on this one's Dismiss. It
     * rises instead when there is no room below, and is pushed back on screen when a phone has
     * scrolled the table so far that the left has no room either. Fixed, because the top layer has no
     * containing block but the viewport - so a scroll would leave it floating away from its row, and
     * scrolling closes it instead.
     */
    const ROW_MENU_GAP = 4;
    const ROW_MENU_EDGE = 8;
    const openRowMenus = () => document.querySelectorAll('[data-row-menu]:popover-open');

    const placeRowMenu = (menu) => {
        const trigger = document.querySelector(`[popovertarget="${menu.id}"]`);
        if (!trigger) {
            return;
        }
        const anchor = trigger.getBoundingClientRect();
        const viewportWidth = document.documentElement.clientWidth;
        menu.style.position = 'fixed';
        menu.style.right = `${Math.max(viewportWidth - anchor.left + ROW_MENU_GAP, ROW_MENU_EDGE)}px`;
        menu.style.top = `${anchor.top}px`;
        menu.style.bottom = 'auto';
        // Its size is only known once it is showing, so the two corrections below measure it.
        // "beforetoggle" still sets the first guess, so it is never painted in the middle of the screen.
        if (!menu.matches(':popover-open')) {
            return;
        }
        const box = menu.getBoundingClientRect();
        if (box.left < ROW_MENU_EDGE) {
            menu.style.right = `${Math.max(viewportWidth - box.width - ROW_MENU_EDGE, ROW_MENU_EDGE)}px`;
        }
        if (box.bottom > window.innerHeight && anchor.bottom > box.height) {
            menu.style.top = 'auto';
            menu.style.bottom = `${window.innerHeight - anchor.bottom}px`;
        }
    };

    const rowMenuStep = (menu, step) => {
        menu.querySelectorAll('[data-row-menu-step]').forEach((element) => {
            element.hidden = element.dataset.rowMenuStep !== step;
        });
    };

    // Neither toggle event bubbles, so both are caught on the way down
    document.addEventListener('beforetoggle', (event) => {
        const menu = event.target;
        if (!(menu instanceof HTMLElement) || !menu.matches('[data-row-menu]')) {
            return;
        }
        if (event.newState === 'open') {
            placeRowMenu(menu);
        } else {
            // Closed half-way through asking is the same as "Keep him", so the next open starts over
            rowMenuStep(menu, 'choose');
        }
    }, true);

    document.addEventListener('toggle', (event) => {
        const menu = event.target;
        if (menu instanceof HTMLElement && menu.matches('[data-row-menu]') && event.newState === 'open') {
            placeRowMenu(menu);
        }
    }, true);

    // Capturing, so the table's own sideways scroll box counts as well as the page
    document.addEventListener('scroll', (event) => {
        openRowMenus().forEach((menu) => {
            if (!menu.contains(event.target)) {
                menu.hidePopover();
            }
        });
    }, true);
    window.addEventListener('resize', () => openRowMenus().forEach((menu) => menu.hidePopover()));

    document.addEventListener('click', (event) => {
        const ask = event.target.closest('[data-row-menu-ask]');
        if (ask) {
            const menu = ask.closest('[data-row-menu]');
            rowMenuStep(menu, 'confirm');
            // The question is taller than the list it replaces
            placeRowMenu(menu);
            // The safe answer takes the focus, so an Enter pressed out of habit keeps the man
            menu.querySelector('[data-row-menu-cancel]')?.focus();
            return;
        }
        const cancel = event.target.closest('[data-row-menu-cancel]');
        if (cancel) {
            cancel.closest('[data-row-menu]').hidePopover();
        }
    });

    // Once the confirmed post has answered, whatever it said: a dismissal reloads the list, which takes
    // the menu with it, and a refusal arrives as a toast the open menu would otherwise sit on top of.
    document.body.addEventListener('htmx:afterRequest', (event) => {
        const menu = event.detail.elt.closest('[data-row-menu]');
        if (menu && menu.matches(':popover-open')) {
            menu.hidePopover();
        }
    });

    // The battle log's Saga and Tally tabs. The choice is written onto the "group" around the log
    // rather than into it, because every finished round swaps the log out and would take the choice
    // with it. Delegated from the document for the same reason nothing here binds to the log itself.
    document.addEventListener('click', (event) => {
        const button = event.target.closest('[data-log-tab-button]');
        if (!button) {
            return;
        }
        const group = button.closest('[data-log-tab]');
        group.dataset.logTab = button.dataset.logTabButton;
        group.querySelectorAll('[data-log-tab-button]').forEach((element) => {
            element.setAttribute('aria-selected', String(element === button));
        });
        // Once the fight is decided the log sits folded behind "Blow by blow", under the report. A tab
        // that only switched the account inside a closed fold would be a control with no visible effect,
        // so choosing one opens it.
        const fold = group.querySelector('details');
        if (fold) {
            fold.open = true;
        }
    });
})();
