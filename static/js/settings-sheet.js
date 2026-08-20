"use strict";

const SETTINGS_SECTION_KEY = "roast-settings-section";
const SETTINGS_SECTIONS = ["sensor", "data", "advanced"];
const settingsOverlay = document.getElementById("settingsModal");
const settingsDialog = document.getElementById("settingsDialog");
const settingsTrigger = document.getElementById("settingsButton");
const settingsTabs = Array.from(document.querySelectorAll("[data-settings-section]"));
const settingsPanels = Array.from(document.querySelectorAll("[data-settings-panel]"));

let settingsPreviousFocus = null;
let syncRequestActive = false;
let syncRunActive = false;
let settingsActiveSyncLookup = null;
let confirmationGateCount = 0;

function storedSettingsSection() {
    try {
        const stored = sessionStorage.getItem(SETTINGS_SECTION_KEY);
        return SETTINGS_SECTIONS.includes(stored) ? stored : "sensor";
    } catch (error) {
        return "sensor";
    }
}

function rememberSettingsSection(section) {
    try {
        sessionStorage.setItem(SETTINGS_SECTION_KEY, section);
    } catch (error) {
        // Session storage may be unavailable in privacy-restricted contexts.
    }
}

function selectSettingsSection(section, focusTab = false) {
    const selected = SETTINGS_SECTIONS.includes(section) ? section : "sensor";

    settingsTabs.forEach((tab) => {
        const active = tab.dataset.settingsSection === selected;
        tab.setAttribute("aria-selected", active ? "true" : "false");
        tab.tabIndex = active ? 0 : -1;
        if (active && focusTab) {
            tab.focus();
        }
    });

    settingsPanels.forEach((panel) => {
        panel.hidden = panel.dataset.settingsPanel !== selected;
    });

    rememberSettingsSection(selected);
}

function visibleSettingsControls() {
    const selector = [
        "button:not([disabled])",
        "input:not([disabled])",
        "select:not([disabled])",
        "textarea:not([disabled])",
        "a[href]",
        "summary",
        "[tabindex]:not([tabindex='-1'])",
    ].join(",");

    return Array.from(settingsDialog.querySelectorAll(selector)).filter((element) => (
        !element.closest("[hidden]")
        && element.getAttribute("aria-hidden") !== "true"
        && element.getClientRects().length > 0
    ));
}

function containSettingsFocus(event) {
    const controls = visibleSettingsControls();
    if (!controls.length) {
        event.preventDefault();
        settingsDialog.focus();
        return;
    }

    const first = controls[0];
    const last = controls[controls.length - 1];
    if (!settingsDialog.contains(document.activeElement)) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
    } else if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
    }
}

function openSettingsModal() {
    if (!settingsOverlay.hidden) {
        return;
    }

    settingsPreviousFocus = document.activeElement;
    settingsOverlay.hidden = false;
    document.body.classList.add("settings-sheet-open");
    settingsTrigger.setAttribute("aria-expanded", "true");

    const section = storedSettingsSection();
    selectSettingsSection(section);
    requestAnimationFrame(() => {
        const selectedTab = settingsTabs.find(
            (tab) => tab.dataset.settingsSection === section
        );
        selectedTab?.focus();
    });

    loadDbSettings();
    loadSensorSettings();
    loadActiveSync();
}

function closeSettingsModal(returnFocus = true) {
    if (settingsOverlay.hidden) {
        return;
    }

    settingsOverlay.hidden = true;
    document.body.classList.remove("settings-sheet-open");
    settingsTrigger.setAttribute("aria-expanded", "false");

    if (returnFocus && settingsPreviousFocus?.isConnected) {
        queueMicrotask(() => settingsPreviousFocus.focus());
    }
}

function handleSettingsTabKeydown(event) {
    const currentIndex = settingsTabs.indexOf(event.currentTarget);
    let nextIndex = currentIndex;

    if (event.key === "ArrowRight") {
        nextIndex = (currentIndex + 1) % settingsTabs.length;
    } else if (event.key === "ArrowLeft") {
        nextIndex = (currentIndex - 1 + settingsTabs.length) % settingsTabs.length;
    } else if (event.key === "Home") {
        nextIndex = 0;
    } else if (event.key === "End") {
        nextIndex = settingsTabs.length - 1;
    } else {
        return;
    }

    event.preventDefault();
    selectSettingsSection(settingsTabs[nextIndex].dataset.settingsSection, true);
}

function handleSettingsKeydown(event) {
    if (settingsOverlay.hidden) {
        return;
    }
    if (event.key === "Escape") {
        event.preventDefault();
        closeSettingsModal();
    } else if (event.key === "Tab") {
        containSettingsFocus(event);
    }
}

function setStatusClass(element, className = "") {
    element.classList.remove("status-success", "status-error");
    if (className) {
        element.classList.add(className);
    }
}

async function loadSensorSettings() {
    const statusText = document.getElementById("sensorStatusText");
    try {
        const response = await fetch("/api/settings/sensor");
        const data = await response.json();
        document.getElementById("sensorUrl").value = data.url || "";
    } catch (error) {
        statusText.textContent = "Unable to load sensor settings";
        setStatusClass(statusText, "status-error");
    }
}

async function saveSensorUrl() {
    const url = document.getElementById("sensorUrl").value.trim();
    const statusText = document.getElementById("sensorStatusText");
    try {
        const response = await fetch("/api/settings/sensor", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url }),
        });
        const data = await response.json();
        if (data.success) {
            statusText.textContent = "Sensor URL saved";
            setStatusClass(statusText, "status-success");
            showToast("Sensor URL saved", "success");
        } else {
            statusText.textContent = "Failed to save sensor URL";
            setStatusClass(statusText, "status-error");
            showToast("Failed to save sensor URL", "error");
        }
    } catch (error) {
        statusText.textContent = "Error saving sensor URL";
        setStatusClass(statusText, "status-error");
        showToast("Error saving sensor URL", "error");
    }
}

async function testSensorConnection() {
    const statusText = document.getElementById("sensorStatusText");
    statusText.textContent = "Testing...";
    setStatusClass(statusText);

    try {
        const response = await fetch("/api/temp/test_connection");
        const data = await response.json();

        if (data.status === "success" && data.temperature !== null) {
            statusText.textContent = data.message
                || `Connected! Current temp: ${data.temperature}°C`;
            setStatusClass(statusText, "status-success");
        } else if (data.sensor_status === "fault") {
            statusText.textContent = data.message || "Sensor hardware fault";
            setStatusClass(statusText, "status-error");
        } else {
            statusText.textContent = data.message
                || "Not connected or sensor unavailable";
            setStatusClass(statusText, "status-error");
        }
    } catch (error) {
        statusText.textContent = "Connection test failed";
        setStatusClass(statusText, "status-error");
    }
}

async function loadDbSettings() {
    const mode = document.getElementById("currentDbMode");
    try {
        const response = await fetch("/api/settings/db");
        const data = await response.json();
        mode.textContent = data.e2e_mode
            ? `${data.mode} (${data.local_database} / ${data.test_run_id})`
            : data.mode;
        document.getElementById("dbModeOnline").disabled = data.e2e_mode;
        document.getElementById("dbModeLocal").checked = data.mode === "local";
        document.getElementById("dbModeOnline").checked = data.mode !== "local";
        setStatusClass(mode, "status-success");
    } catch (error) {
        mode.textContent = "Unavailable";
        setStatusClass(mode, "status-error");
    }
}

async function changeDbMode(event) {
    const newMode = event.target.value;
    try {
        const response = await fetch("/api/settings/db", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mode: newMode }),
        });
        const data = await response.json();
        if (data.success) {
            document.getElementById("currentDbMode").textContent = data.mode;
            showToast(`Switched to ${data.mode} database`, "success");
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast("Error switching database", "error");
            await loadDbSettings();
        }
    } catch (error) {
        showToast("Error switching database", "error");
        await loadDbSettings();
    }
}

function replaceButtonLabel(button, iconName, label) {
    const icon = document.createElement("span");
    icon.className = "material-icons";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = iconName;
    button.replaceChildren(icon, document.createTextNode(label));
}

function setSyncPreviewButtons(disabled, busy = false) {
    const onlineButton = document.getElementById("syncOnlineToLocalBtn");
    const localButton = document.getElementById("syncLocalToOnlineBtn");
    onlineButton.disabled = disabled;
    localButton.disabled = disabled;

    if (busy) {
        replaceButtonLabel(onlineButton, "sync", "Preflight running...");
        replaceButtonLabel(localButton, "sync", "Preflight running...");
        onlineButton.querySelector(".material-icons").classList.add("spinning");
        localButton.querySelector(".material-icons").classList.add("spinning");
        return;
    }

    replaceButtonLabel(onlineButton, "cloud_download", "Preview Online → Local");
    replaceButtonLabel(localButton, "cloud_upload", "Preview Local → Online");
}

function appendPreflightLine(container, label, value) {
    const line = document.createElement("p");
    const title = document.createElement("strong");
    title.textContent = `${label}: `;
    line.appendChild(title);
    line.appendChild(document.createTextNode(value));
    container.appendChild(line);
}

function syncErrorText(data, fallback) {
    if (typeof data?.error === "string") {
        return data.error;
    }
    return data?.error?.message || fallback;
}

function focusVisibleSyncControl(control) {
    const panel = control.closest("[data-settings-panel]");
    if (!settingsOverlay.hidden && panel && !panel.hidden) {
        queueMicrotask(() => control.focus());
    }
}

function appendConfirmationGate(container, token, label, handler, cancelHandler = null) {
    confirmationGateCount += 1;
    const inputId = `settingsSyncConfirmation${confirmationGateCount}`;
    const gate = document.createElement("div");
    gate.className = "sync-confirmation-gate";

    const instruction = document.createElement("label");
    instruction.className = "settings-hint";
    instruction.htmlFor = inputId;
    instruction.textContent = `Type the exact confirmation ${token}`;
    gate.appendChild(instruction);

    const required = document.createElement("code");
    required.className = "sync-confirmation-token";
    required.textContent = token;
    gate.appendChild(required);

    const input = document.createElement("input");
    input.id = inputId;
    input.type = "text";
    input.className = "input-field";
    input.autocomplete = "off";
    input.spellcheck = false;
    input.setAttribute("aria-label", `Type ${token}`);
    gate.appendChild(input);

    const actions = document.createElement("div");
    actions.className = "sync-gate-actions";
    const submit = document.createElement("button");
    submit.type = "button";
    submit.className = "btn btn-secondary";
    submit.textContent = label;
    submit.addEventListener("click", () => handler(input.value));
    actions.appendChild(submit);

    if (cancelHandler) {
        const cancel = document.createElement("button");
        cancel.type = "button";
        cancel.className = "btn btn-secondary";
        cancel.textContent = "Cancel run";
        cancel.addEventListener("click", cancelHandler);
        actions.appendChild(cancel);
    }

    gate.appendChild(actions);
    container.appendChild(gate);
    focusVisibleSyncControl(input);
}

function beginSyncResult(statusClass = "") {
    const result = document.getElementById("syncPreflightResult");
    const containedFocus = result.contains(document.activeElement);
    result.replaceChildren();
    result.hidden = false;
    result.className = "sync-preflight-result";
    result.tabIndex = -1;
    if (statusClass) {
        result.classList.add(statusClass);
    }
    if (containedFocus) {
        focusVisibleSyncControl(result);
    }
    return result;
}

function renderSyncPreflight(data) {
    if (!data.audit_recorded) {
        const result = beginSyncResult("status-error");
        appendPreflightLine(
            result,
            "Audit failure",
            data.audit_error?.message || "The preflight audit record was not persisted."
        );
        return;
    }
    if (!data.success || !data.plan) {
        const result = beginSyncResult("status-error");
        appendPreflightLine(
            result,
            "Preflight failed",
            data.error?.message || "The sanitized plan is unavailable."
        );
        appendPreflightLine(result, "Audit record", data.audit_path);
        return;
    }

    const plan = data.plan;
    const result = beginSyncResult("status-success");
    appendPreflightLine(result, "Run ID", plan.run_id);
    appendPreflightLine(
        result,
        "Source",
        `${plan.source.role} (${plan.source.host}/${plan.source.database})`
    );
    appendPreflightLine(
        result,
        "Destination",
        `${plan.destination.role} (${plan.destination.host}/${plan.destination.database})`
    );
    appendPreflightLine(result, "Source counts", JSON.stringify(plan.source_counts));
    appendPreflightLine(
        result,
        "Destination counts",
        JSON.stringify(plan.destination_counts)
    );
    appendPreflightLine(
        result,
        "Backup scope",
        `${plan.backup.scope}: ${plan.backup.collections.join(", ") || "empty database"}`
    );
    appendPreflightLine(result, "CLI command", plan.cli_command);
    appendPreflightLine(result, "Preflight audit", data.audit_path);

    if (!data.apply_eligible) {
        appendPreflightLine(
            result,
            "Applied sync",
            "Guarded CLI only from this connection."
        );
        return;
    }

    syncRunActive = true;
    setSyncPreviewButtons(true);
    appendConfirmationGate(
        result,
        data.backup_confirmation,
        "Create complete backup",
        (confirmation) => runSyncBackup(plan.run_id, plan.direction, confirmation)
    );
}

function renderAwaitingApply(data, phaseError = null) {
    syncRunActive = true;
    setSyncPreviewButtons(true);
    const result = beginSyncResult("status-success");
    appendPreflightLine(result, "Run ID", data.run_id);
    appendPreflightLine(result, "Direction", data.direction);
    appendPreflightLine(
        result,
        data.restored ? "State" : "Backup",
        data.restored ? "Restored and re-verified" : "Complete and verified"
    );
    appendPreflightLine(
        result,
        "Backup summary",
        `${data.backup.collection_count} collections, ${data.backup.document_count} documents`
    );
    appendPreflightLine(
        result,
        "Verified manifest SHA-256",
        data.backup.manifest_sha256 || "unavailable"
    );
    appendPreflightLine(result, "Backup path", data.backup.path);
    if (phaseError) {
        appendPreflightLine(
            result,
            "Sync request failed",
            syncErrorText(phaseError, "The guarded sync request failed.")
        );
    }
    appendConfirmationGate(
        result,
        data.apply_confirmation,
        "Apply synchronization",
        (confirmation) => runSyncApply(data.run_id, data.direction, confirmation),
        () => runSyncCancel(data.run_id, data.direction)
    );
}

function renderSyncTerminal(data) {
    syncRunActive = false;
    setSyncPreviewButtons(false);
    const successful = data.status === "success"
        || data.status === "cancelled_after_backup";
    const result = beginSyncResult(successful ? "status-success" : "status-error");
    appendPreflightLine(result, "Run ID", data.run_id);
    appendPreflightLine(result, "Status", data.status);
    if (data.backup) {
        appendPreflightLine(result, "Backup path", data.backup.path);
    }
    if (data.sync?.collections) {
        Object.entries(data.sync.collections).forEach(([name, outcome]) => {
            appendPreflightLine(
                result,
                `${name.charAt(0).toUpperCase()}${name.slice(1)} outcome`,
                JSON.stringify(outcome)
            );
        });
    }
    if (data.sync?.aggregate) {
        appendPreflightLine(result, "Sync totals", JSON.stringify(data.sync.aggregate));
    }
    if (data.error) {
        appendPreflightLine(result, "Failure", syncErrorText(data, "Sync failed"));
    }
    if (data.audit_path) {
        appendPreflightLine(result, "Audit record", data.audit_path);
    }
    if (data.recovery_path) {
        appendPreflightLine(result, "Audit recovery", data.recovery_path);
    }
}

function renderSyncPhaseError(data, preserveRun = false) {
    if (data.stage !== "recovery_required" && !preserveRun) {
        syncRunActive = false;
        setSyncPreviewButtons(false);
    } else {
        syncRunActive = true;
        setSyncPreviewButtons(true);
    }
    const result = beginSyncResult("status-error");
    appendPreflightLine(
        result,
        data.stage === "recovery_required" ? "Recovery required" : "Sync request failed",
        syncErrorText(data, "The guarded sync request failed.")
    );
    if (data.run_id) {
        appendPreflightLine(result, "Run ID", data.run_id);
    }
}

async function syncMutation(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    return { response, data: await response.json() };
}

async function requestActiveSync(phaseError = null) {
    const expectedExistingRun = syncRunActive;
    try {
        const response = await fetch("/api/sync/runs/active");
        const data = await response.json();
        if (response.ok && data.active) {
            renderAwaitingApply(data.active, phaseError);
        } else if (
            response.ok
            && !data.active
            && expectedExistingRun
            && syncRunActive
            && !syncRequestActive
        ) {
            syncRunActive = false;
            setSyncPreviewButtons(false);
            const result = document.getElementById("syncPreflightResult");
            result.replaceChildren();
            result.hidden = true;
            result.className = "sync-preflight-result";
        } else if (!response.ok) {
            renderSyncPhaseError(data);
        }
    } catch (error) {
        renderSyncPhaseError({
            stage: "recovery_required",
            error: "Unable to determine whether a guarded sync is active.",
        });
    }
}

async function loadActiveSync(phaseError = null) {
    if (settingsActiveSyncLookup) {
        return settingsActiveSyncLookup;
    }

    const lookup = requestActiveSync(phaseError);
    settingsActiveSyncLookup = lookup;
    try {
        return await lookup;
    } finally {
        if (settingsActiveSyncLookup === lookup) {
            settingsActiveSyncLookup = null;
        }
    }
}

async function syncData(direction) {
    if (syncRequestActive || syncRunActive) {
        return;
    }
    syncRequestActive = true;
    setSyncPreviewButtons(true, true);

    try {
        const response = await fetch(`/api/sync/preflight/${direction}`, {
            method: "POST",
        });
        const data = await response.json();
        renderSyncPreflight(data);
        showToast(
            data.success && data.audit_recorded
                ? "Read-only sync preflight recorded"
                : "Sync preflight needs attention",
            data.success && data.audit_recorded ? "success" : "error"
        );
    } catch (error) {
        renderSyncPreflight({
            success: false,
            audit_recorded: false,
            audit_error: {
                message: "Network failure; audit persistence is unknown.",
            },
        });
        showToast("Sync preflight failed: Network error", "error");
    } finally {
        syncRequestActive = false;
        if (!syncRunActive) {
            setSyncPreviewButtons(false);
        }
    }
}

async function runSyncBackup(runId, direction, confirmation) {
    if (syncRequestActive) {
        return;
    }
    syncRequestActive = true;
    try {
        const { data } = await syncMutation(
            `/api/sync/runs/${runId}/backup`,
            { direction, confirmation }
        );
        if (data.stage === "awaiting_apply") {
            renderAwaitingApply(data);
            showToast("Destination backup complete and verified", "success");
        } else if (data.stage === "terminal") {
            renderSyncTerminal(data);
            showToast("Backup phase needs attention", "error");
        } else {
            renderSyncPhaseError(data);
            await loadActiveSync();
            showToast("Backup confirmation rejected", "error");
        }
    } catch (error) {
        renderSyncPhaseError({
            stage: "recovery_required",
            run_id: runId,
            error: "Network failure during backup; inspect the saved run before continuing.",
        });
    } finally {
        syncRequestActive = false;
    }
}

async function runSyncApply(runId, direction, confirmation) {
    if (syncRequestActive) {
        return;
    }
    syncRequestActive = true;
    try {
        const { data } = await syncMutation(
            `/api/sync/runs/${runId}/apply`,
            { direction, confirmation }
        );
        if (data.stage === "terminal") {
            renderSyncTerminal(data);
            showToast(
                data.status === "success"
                    ? "Database sync complete"
                    : "Database sync needs attention",
                data.status === "success" ? "success" : "error"
            );
        } else {
            await loadActiveSync(data);
            showToast("Apply confirmation rejected", "error");
        }
    } catch (error) {
        renderSyncPhaseError({
            stage: "recovery_required",
            run_id: runId,
            error: "Network failure during apply; inspect the saved run before retrying.",
        });
    } finally {
        syncRequestActive = false;
    }
}

async function runSyncCancel(runId, direction) {
    if (syncRequestActive) {
        return;
    }
    syncRequestActive = true;
    try {
        const { data } = await syncMutation(
            `/api/sync/runs/${runId}/cancel`,
            { direction }
        );
        if (data.stage === "terminal") {
            renderSyncTerminal(data);
            const cancelled = data.status === "cancelled_after_backup";
            showToast(
                cancelled
                    ? "Guarded sync cancelled; backup retained"
                    : "Cancellation audit needs recovery attention",
                cancelled ? "success" : "error"
            );
        } else {
            await loadActiveSync(data);
            showToast("Cancellation request rejected", "error");
        }
    } catch (error) {
        renderSyncPhaseError({
            stage: "recovery_required",
            run_id: runId,
            error: "Network failure during cancellation; inspect the saved run.",
        });
    } finally {
        syncRequestActive = false;
    }
}

function announceAdvancedResult(message, type) {
    const status = document.getElementById("settingsActionStatus");
    status.hidden = false;
    status.textContent = message;
    setStatusClass(status, type === "success" ? "status-success" : "status-error");
    showToast(message, type);
}

async function cleanTestData() {
    if (!confirm("Delete all test data (documents marked with test_data flag) from local database?")) {
        return;
    }

    const button = document.getElementById("cleanTestDataBtn");
    button.disabled = true;
    replaceButtonLabel(button, "science", "Deleting...");
    button.querySelector(".material-icons").classList.add("spinning");

    try {
        const response = await fetch("/api/db/clean-test-data", { method: "POST" });
        const data = await response.json();

        if (data.success) {
            let message = `Test data cleaned! ${data.beans_deleted} beans, ${data.roasts_deleted} roasts`;
            if (data.temp_logs_deleted > 0) {
                message += `, ${data.temp_logs_deleted} temp logs`;
            }
            announceAdvancedResult(`${message} deleted.`, "success");
        } else {
            announceAdvancedResult(`Failed: ${data.error}`, "error");
        }
    } catch (error) {
        announceAdvancedResult("Failed: Network error", "error");
    } finally {
        button.disabled = false;
        replaceButtonLabel(button, "science", "Clean Up Test Data");
    }
}

async function cleanLocalDb() {
    if (!confirm("Are you sure you want to delete ALL beans and roasts from your LOCAL database?")) {
        return;
    }
    if (!confirm("⚠️ FINAL WARNING: This action CANNOT be undone. Type \"DELETE\" mentally and click OK to proceed.")) {
        return;
    }

    const button = document.getElementById("cleanLocalDbBtn");
    button.disabled = true;
    replaceButtonLabel(button, "delete_forever", "Deleting...");
    button.querySelector(".material-icons").classList.add("spinning");

    try {
        const response = await fetch("/api/db/clean-local", { method: "POST" });
        const data = await response.json();

        if (data.success) {
            announceAdvancedResult(
                `Local DB cleaned! ${data.beans_deleted} beans and ${data.roasts_deleted} roasts deleted.`,
                "success"
            );
        } else {
            announceAdvancedResult(`Failed: ${data.error}`, "error");
        }
    } catch (error) {
        announceAdvancedResult("Failed: Network error", "error");
    } finally {
        button.disabled = false;
        replaceButtonLabel(button, "delete_forever", "Clean Up Local DB");
    }
}

settingsTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        selectSettingsSection(tab.dataset.settingsSection);
    });
    tab.addEventListener("keydown", handleSettingsTabKeydown);
});

document.querySelectorAll('input[name="dbMode"]').forEach((radio) => {
    radio.addEventListener("change", changeDbMode);
});

settingsOverlay.addEventListener("click", (event) => {
    if (event.target === settingsOverlay) {
        closeSettingsModal();
    }
});

document.addEventListener("keydown", handleSettingsKeydown);
