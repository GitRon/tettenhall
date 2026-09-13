/*
 * Everything the pages need from JavaScript: the CSRF header htmx has to send, the toasts, and the
 * account menu in the navbar. A static file rather than a block in "base.html", so nothing here is
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
})();
