/**
 * Shared Flatpickr date picker initialization.
 * Apply to any input with data-flatpickr attribute.
 *
 * Attributes:
 *   data-flatpickr         - Enable Flatpickr on this element
 *   data-flatpickr-mode    - "date" (default) or "datetime"
 *   data-flatpickr-default-today - If "true", default to today when empty
 */
(function () {
    function getTodayStr() {
        return new Date().toISOString().slice(0, 10);
    }

    function initDatePickers() {
        var els = document.querySelectorAll('[data-flatpickr]');
        els.forEach(function (el) {
            if (el._flatpickr) return;

            var mode = el.getAttribute('data-flatpickr-mode') || 'date';
            var defaultToday = el.getAttribute('data-flatpickr-default-today') === 'true';
            var onchangeName = el.getAttribute('data-flatpickr-onchange');

            var opts = {
                allowInput: false,
                disableMobile: true,
                monthSelectorType: 'static',
                shorthandCurrentMonth: true,
            };

            if (mode === 'datetime') {
                opts.enableTime = true;
                opts.dateFormat = 'Y-m-d\\TH:i';
                opts.time_24hr = true;
            } else {
                opts.dateFormat = 'Y-m-d';
            }

            if (defaultToday && !el.value) {
                el.value = mode === 'datetime'
                    ? new Date().toISOString().slice(0, 16)
                    : getTodayStr();
            }

            if (onchangeName && typeof window[onchangeName] === 'function') {
                opts.onChange = window[onchangeName];
            }

            flatpickr(el, opts);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDatePickers);
    } else {
        initDatePickers();
    }

    window.initDatePickers = initDatePickers;
})();
