(() => {
    const form = document.querySelector('.management-form--bean');
    const rows = document.getElementById('purchaseRows');
    const error = document.getElementById('beanFormError');
    document.getElementById('addPurchase').addEventListener('click', () => {
        rows.append(document.getElementById('purchaseRowTemplate').content.cloneNode(true));
        rows.lastElementChild.querySelector('input[type="date"]').focus();
    });
    rows.addEventListener('click', event => {
        const button = event.target.closest('.remove-purchase');
        if (!button) return;
        const row = button.closest('.purchase-row');
        row.remove();
        document.getElementById('addPurchase').focus();
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
