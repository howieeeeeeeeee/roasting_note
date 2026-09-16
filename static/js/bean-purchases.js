(() => {
    const form = document.querySelector('.management-form--bean');
    const rows = document.getElementById('purchaseRows');
    const error = document.getElementById('beanFormError');
    document.getElementById('addPurchase').addEventListener('click', () => {
        rows.append(document.getElementById('purchaseRowTemplate').content.cloneNode(true));
        rows.lastElementChild.querySelector('input[type="date"]').focus();
    });
    rows.addEventListener('click', event => {
        const button = event.target.closest('button');
        const row = button?.closest('.purchase-row');
        if (!row) return;
        const panel = row.querySelector('.purchase-removal');
        const remove = row.querySelector('.remove-purchase');
        if (button === remove) {
            const date = row.querySelector('[name="purchase_date"]').value;
            const weight = row.querySelector('[name="purchase_weight_grams"]').value;
            row.querySelector('.purchase-removal-summary').textContent =
                `Remove this purchase${date ? ` dated ${date}` : ''}${weight ? ` (${weight}g)` : ''}?`;
            panel.hidden = false;
            remove.setAttribute('aria-expanded', 'true');
            panel.querySelector('.cancel-purchase-removal').focus();
        } else if (button.matches('.cancel-purchase-removal')) {
            panel.hidden = true;
            remove.setAttribute('aria-expanded', 'false');
            remove.focus();
        } else if (button.matches('.confirm-purchase-removal') && !panel.hidden) {
            const next = row.nextElementSibling || row.previousElementSibling;
            row.remove();
            (next?.querySelector('.remove-purchase') || document.getElementById('addPurchase')).focus();
        }
    });
    form.addEventListener('submit', async event => {
        event.preventDefault();
        const submit = form.querySelector('button[type="submit"]');
        if (submit.disabled) return;
        submit.disabled = true;
        error.hidden = true;
        try {
            const response = await fetch(form.action, {method: 'POST', body: new FormData(form)});
            if (!response.ok) {
                const result = await response.json();
                throw new Error(result.error || 'Unable to save the bean.');
            }
            window.location.assign(response.url);
        } catch (failure) {
            error.textContent = failure.message || 'Unable to save. Check your connection and retry.';
            error.hidden = false;
            error.scrollIntoView({block: 'center'});
            submit.disabled = false;
        }
    });
})();
