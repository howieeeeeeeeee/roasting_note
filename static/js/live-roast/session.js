const SYNC_INTERVAL_MS = 1000;

export function formatTime(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export function defaultRoastTitle(title, beanName) {
    if (!/^(?:untitled(?: roast)?)?$/i.test(title.trim())) return title;
    const words = (beanName || "").trim().split(/\s+/);
    return words[0] ? words.slice(-2).join(" ") : title;
}

export function createSession(config, chart) {
    const elements = {
        timerDisplay: document.getElementById("timerDisplay"),
        startBtn: document.getElementById("startBtn"),
        endBtn: document.getElementById("endBtn"),
        completeDraftBtn: document.getElementById("completeDraftBtn"),
        eventButtons: document.querySelectorAll(".event-btn-compact"),
        addEventBtn: document.getElementById("addEventBtn"),
        timelineList: document.getElementById("timelineList"),
        roastTitleInput: document.getElementById("roast_title"),
        tempValueDisplay: document.getElementById("tempValue"),
        tempSensorStatus: document.getElementById("tempSensorStatus"),
        tempInput: document.getElementById("temperature"),
        rorDisplay: document.getElementById("rorValue"),
    };
    const state = {
        timerInterval: null,
        syncInterval: null,
        syncLoopActive: false,
        syncInFlight: false,
        seconds: 0,
        isRunning: false,
        setupLocked: config.roastStarted || config.roastEnded,
        setupCollapsed: false,
        setupSaveTimer: null,
        lastTemp: null,
        lastTempIsStale: true,
        lastFan: 9,
        lastPower: 3,
        fcStartTime: null,
    };
    let setupSave = Promise.resolve(true);
    let displayListener = () => {};

    function notifyDisplayChange() {
        displayListener();
    }

    function setDisplayListener(listener) {
        displayListener = listener || (() => {});
    }

    function updateTimer() {
        state.seconds += 1;
        elements.timerDisplay.textContent = formatTime(state.seconds);
        updateFcDisplay();
    }

    function updateFcDisplay() {
        if (state.fcStartTime !== null) {
            const tile = document.getElementById("fcElapsedTile");
            if (tile) tile.style.display = "flex";
            const elapsed = state.seconds - state.fcStartTime;
            const display = document.getElementById("fcElapsedValue");
            if (display) display.textContent = formatTime(Math.max(0, elapsed));
        }
        notifyDisplayChange();
    }

    function adjustFan(delta) {
        const input = document.getElementById("fan_setting");
        const display = document.getElementById("fanValue");
        const nextValue = Math.max(
            1,
            Math.min(9, (parseInt(input.value, 10) || 9) + delta),
        );
        input.value = nextValue;
        display.textContent = nextValue;
        state.lastFan = nextValue;
        notifyDisplayChange();
    }

    function adjustPower(delta) {
        const input = document.getElementById("power_setting");
        const display = document.getElementById("powerValue");
        const nextValue = Math.max(
            1,
            Math.min(9, (parseInt(input.value, 10) || 3) + delta),
        );
        input.value = nextValue;
        display.textContent = nextValue;
        state.lastPower = nextValue;
        notifyDisplayChange();
    }

    function toggleSetup() {
        const content = document.getElementById("setupContent");
        const icon = document.getElementById("setupToggleIcon");
        state.setupCollapsed = !state.setupCollapsed;
        content.style.display = state.setupCollapsed ? "none" : "block";
        icon.textContent = state.setupCollapsed ? "expand_more" : "expand_less";
    }

    function collapseSetupOnStart() {
        if (!state.setupCollapsed) toggleSetup();
    }

    function collectSetupData() {
        return {
            title: elements.roastTitleInput.value || "Untitled Roast",
            bean_id: document.getElementById("bean_id").value || null,
            original_weight_grams:
                document.getElementById("original_weight").value || null,
            ambient_temp_celsius:
                document.getElementById("ambient_temp").value || null,
            ambient_humidity:
                document.getElementById("ambient_humidity").value || null,
        };
    }

    function saveSetupFields() {
        if (state.setupLocked) return Promise.resolve(false);
        const payload = JSON.stringify(collectSetupData());
        setupSave = setupSave.then(async () => {
            try {
                const response = await fetch(`/api/roast/update_setup/${config.roastId}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: payload,
                });
                if (!response.ok) throw new Error("Unable to save roast setup");
                return true;
            } catch (error) {
                console.error("Error saving roast setup:", error);
                showMessage("Unable to save roast setup. Please retry.", "error");
                return false;
            }
        });
        return setupSave;
    }

    function scheduleSetupSave() {
        if (state.setupLocked) return;
        if (state.setupSaveTimer) clearTimeout(state.setupSaveTimer);
        state.setupSaveTimer = setTimeout(saveSetupFields, 500);
    }

    function getUsableTemperature() {
        if (elements.tempInput && elements.tempInput.value) {
            return parseInt(elements.tempInput.value, 10);
        }
        return state.lastTempIsStale ? null : state.lastTemp;
    }

    function setSensorStatus(status, ageSeconds) {
        if (!elements.tempSensorStatus) return;
        elements.tempSensorStatus.className =
            `sensor-status sensor-status-${status || "idle"}`;
        const labels = {
            ok: "Live",
            retrying: "Retrying",
            fault: "Sensor fault",
            offline: "Offline",
        };
        if (status === "stale") {
            elements.tempSensorStatus.textContent =
                ageSeconds !== null && ageSeconds !== undefined
                    ? `Stale ${ageSeconds}s`
                    : "Stale";
        } else {
            elements.tempSensorStatus.textContent = labels[status] || "Idle";
        }
    }

    function updateTemperatureDisplay(data) {
        const status =
            data.sensor_status ||
            (data.temperature !== null ? "ok" : "offline");
        if (data.temperature !== null && data.temperature !== undefined) {
            elements.tempValueDisplay.textContent = data.temperature;
            elements.tempValueDisplay.style.color = "";
            state.lastTemp = data.temperature;
            state.lastTempIsStale = false;
            if (elements.tempInput) elements.tempInput.value = data.temperature;
        } else if (state.lastTemp !== null && status === "retrying") {
            elements.tempValueDisplay.style.color = "#f0ad4e";
            state.lastTempIsStale = false;
        } else if (state.lastTemp !== null) {
            elements.tempValueDisplay.style.color = "#d9534f";
            state.lastTempIsStale = true;
            if (elements.tempInput) elements.tempInput.value = "";
        } else {
            elements.tempValueDisplay.textContent = "--";
            elements.tempValueDisplay.style.color = "#999";
            state.lastTempIsStale = true;
            if (elements.tempInput) elements.tempInput.value = "";
        }
        setSensorStatus(status, data.last_success_age_seconds);
        notifyDisplayChange();
    }

    function addLogToTimeline(time, temperature, fan, power, ror) {
        const emptyLog = elements.timelineList.querySelector(".empty-log");
        if (emptyLog) emptyLog.remove();
        const item = document.createElement("div");
        item.className = "timeline-item timeline-temp";
        const rorText =
            ror !== null && ror !== undefined
                ? ` (${ror.toFixed(1)}°C/min)`
                : "";
        item.innerHTML = `
            <div class="timeline-time">${formatTime(time)}</div>
            <div class="timeline-content">
                <span class="timeline-temp-value">${temperature}°C${rorText}</span>
                <span class="timeline-settings">Fan: ${fan} | Power: ${power}</span>
            </div>
        `;
        elements.timelineList.insertBefore(item, elements.timelineList.firstChild);
    }

    function scheduleNextSync(startedAt) {
        if (!state.syncLoopActive) return;
        const delay = Math.max(250, SYNC_INTERVAL_MS - (Date.now() - startedAt));
        state.syncInterval = setTimeout(syncState, delay);
    }

    async function syncState() {
        if (!elements.tempValueDisplay || state.syncInFlight) return;
        const startedAt = Date.now();
        state.syncInFlight = true;
        const fanInput = document.getElementById("fan_setting");
        const powerInput = document.getElementById("power_setting");
        const fan = fanInput ? parseInt(fanInput.value, 10) || 0 : 0;
        const power = powerInput ? parseInt(powerInput.value, 10) || 0 : 0;
        try {
            const response = await fetch(
                `/api/roast/sync_state/${config.roastId}`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        time_seconds: state.seconds,
                        status: state.isRunning ? "running" : "stopped",
                        fan_setting: fan,
                        power_setting: power,
                    }),
                },
            );
            const data = await response.json();
            updateTemperatureDisplay(data);
            if (data.success && data.temperature !== null) {
                if (data.ror !== null) {
                    elements.rorDisplay.textContent = data.ror.toFixed(1);
                    elements.rorDisplay.style.color = "";
                } else {
                    elements.rorDisplay.textContent = "--";
                    elements.rorDisplay.style.color = "#999";
                }
                if (data.logged_to_db) {
                    addLogToTimeline(
                        state.seconds,
                        data.temperature,
                        fan,
                        power,
                        data.ror,
                    );
                    chart.updateData(
                        state.seconds,
                        data.temperature,
                        data.ror,
                        fan,
                        power,
                    );
                }
            }
        } catch (error) {
            console.error("Error in sync loop:", error);
            updateTemperatureDisplay({
                temperature: null,
                sensor_status: state.lastTemp === null ? "offline" : "stale",
                last_success_age_seconds: null,
            });
        } finally {
            state.syncInFlight = false;
            notifyDisplayChange();
            scheduleNextSync(startedAt);
        }
    }

    function startSyncLoop() {
        stopSyncLoop();
        state.syncLoopActive = true;
        syncState();
    }

    function stopSyncLoop() {
        state.syncLoopActive = false;
        if (state.syncInterval) {
            clearTimeout(state.syncInterval);
            state.syncInterval = null;
        }
    }

    function showMessage(message, kind) {
        if (window.showToast) window.showToast(message, kind);
    }

    function wireSetupPersistence() {
        if (state.setupLocked) return;
        const beanSelect = document.getElementById("bean_id");
        const fillTitle = () => {
            elements.roastTitleInput.value = defaultRoastTitle(
                elements.roastTitleInput.value,
                beanSelect.selectedOptions[0]?.dataset.beanName,
            );
        };
        beanSelect.addEventListener("input", fillTitle);
        beanSelect.addEventListener("change", fillTitle);
        [
            "roast_title",
            "bean_id",
            "original_weight",
            "ambient_temp",
            "ambient_humidity",
        ].forEach((fieldId) => {
            const field = document.getElementById(fieldId);
            if (!field) return;
            field.addEventListener("input", scheduleSetupSave);
            field.addEventListener("change", saveSetupFields);
            field.addEventListener("blur", saveSetupFields);
        });
        window.addEventListener("pagehide", () => {
            if (state.setupLocked) return;
            const payload = JSON.stringify(collectSetupData());
            if (navigator.sendBeacon) {
                navigator.sendBeacon(
                    `/api/roast/update_setup/${config.roastId}`,
                    new Blob([payload], { type: "application/json" }),
                );
            } else {
                fetch(`/api/roast/update_setup/${config.roastId}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: payload,
                    keepalive: true,
                });
            }
        });
    }

    function wireCompleteDraft() {
        if (!elements.completeDraftBtn) return;
        elements.completeDraftBtn.addEventListener("click", async () => {
            if (elements.completeDraftBtn.disabled) return;
            elements.completeDraftBtn.disabled = true;
            try {
                if (state.setupSaveTimer) {
                    clearTimeout(state.setupSaveTimer);
                    state.setupSaveTimer = null;
                }
                if (!await saveSetupFields()) {
                    elements.completeDraftBtn.disabled = false;
                    return;
                }
                const response = await fetch(
                    `/api/roast/complete_draft/${config.roastId}`,
                    { method: "POST" },
                );
                const data = await response.json();
                if (response.ok && data.success) {
                    window.location.href = `/roast/edit/${config.roastId}`;
                } else {
                    showToast(data.error || "Error completing draft roast. Please try again.", "error");
                    elements.completeDraftBtn.disabled = false;
                }
            } catch (error) {
                console.error("Error:", error);
                showToast("Error completing draft roast. Please try again.", "error");
                elements.completeDraftBtn.disabled = false;
            }
        });
    }

    function wireStart() {
        if (!elements.startBtn) return;
        elements.startBtn.addEventListener("click", async () => {
            if (elements.startBtn.disabled) return;
            const beanId = document.getElementById("bean_id").value;
            const weight = document.getElementById("original_weight").value;
            if (!beanId || !weight) {
                showToast("Please select a bean and enter the green weight before starting.", "error");
                return;
            }
            elements.startBtn.disabled = true;
            try {
                clearTimeout(state.setupSaveTimer);
                if (!await saveSetupFields()) return;
                const response = await fetch(
                    `/api/roast/start/${config.roastId}`,
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            bean_id: beanId,
                            original_weight_grams: weight,
                            ambient_temp_celsius:
                                document.getElementById("ambient_temp").value || null,
                            ambient_humidity:
                                document.getElementById("ambient_humidity").value || null,
                        }),
                    },
                );
                if (!response.ok) {
                    showToast("Error starting roast. Please try again.", "error");
                    return;
                }
                state.isRunning = true;
                state.setupLocked = true;
                state.seconds = 0;
                state.timerInterval = setInterval(updateTimer, 1000);
                elements.startBtn.style.display = "none";
                elements.endBtn.style.display = "inline-flex";
                elements.eventButtons.forEach((button) => {
                    button.disabled = false;
                });
                elements.addEventBtn.disabled = false;
                document.getElementById("bean_id").disabled = true;
                document.getElementById("original_weight").disabled = true;
                collapseSetupOnStart();
                notifyDisplayChange();
            } catch (error) {
                console.error("Error:", error);
                showToast("Error starting roast. Please try again.", "error");
            } finally {
                elements.startBtn.disabled = state.isRunning;
            }
        });
    }

    function wireEnd() {
        if (!elements.endBtn) return;
        elements.endBtn.addEventListener("click", async () => {
            if (elements.endBtn.disabled) return;
            elements.endBtn.disabled = true;
            try {
                const response = await fetch(`/api/roast/end/${config.roastId}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ elapsed_seconds: state.seconds }),
                });
                if (!response.ok) {
                    showToast("Error ending roast. Please try again.", "error");
                    return;
                }
                clearInterval(state.timerInterval);
                state.isRunning = false;
                elements.eventButtons.forEach((button) => {
                    button.disabled = true;
                });
                elements.addEventBtn.disabled = true;
                stopSyncLoop();
                window.location.href = `/roast/edit/${config.roastId}`;
            } catch (error) {
                console.error("Error:", error);
                showToast("Error ending roast. Please try again.", "error");
            } finally {
                if (state.isRunning) elements.endBtn.disabled = false;
            }
        });
    }

    function wireTimingEvents() {
        elements.eventButtons.forEach((button) => {
            button.addEventListener("click", async () => {
                const eventName = button.dataset.event;
                if (button.disabled) return;
                button.disabled = true;
                const eventSeconds = state.seconds;
                const fan = parseInt(
                    document.getElementById("fan_setting").value,
                    10,
                ) || state.lastFan || null;
                const power = parseInt(
                    document.getElementById("power_setting").value,
                    10,
                ) || state.lastPower || null;
                const temperature = getUsableTemperature();
                try {
                    const response = await fetch(
                        `/api/roast/add_timing/${config.roastId}`,
                        {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                event_name: eventName,
                                time_seconds: eventSeconds,
                                temperature,
                                fan_setting: fan,
                                power_setting: power,
                            }),
                        },
                    );
                    const result = await response.json();
                    if (!response.ok || !result.success) {
                        showMessage("Error logging event. Please try again.", "error");
                        return;
                    }
                    if (eventName === "First Crack Start") {
                        state.fcStartTime = eventSeconds;
                        updateFcDisplay();
                    }
                    if (fan !== null) state.lastFan = fan;
                    if (power !== null) state.lastPower = power;
                    const emptyLog =
                        elements.timelineList.querySelector(".empty-log");
                    if (emptyLog) emptyLog.remove();
                    const item = document.createElement("div");
                    item.className = "timeline-item timeline-key";
                    let content =
                        `<strong class="timeline-label">${eventName}</strong>`;
                    if (temperature) {
                        content +=
                            `<span class="timeline-temp-value"> ` +
                            `${temperature}°C</span>`;
                    }
                    content +=
                        `<span class="timeline-settings"> Fan: ${fan || 0} | ` +
                        `Power: ${power || 0}</span>`;
                    item.innerHTML = `
                        <div class="timeline-time">${formatTime(eventSeconds)}</div>
                        <div class="timeline-content">${content}</div>
                    `;
                    elements.timelineList.insertBefore(
                        item,
                        elements.timelineList.firstChild,
                    );
                    chart.addEventMarker(eventSeconds, eventName);
                    showMessage(
                        `✓ ${eventName} logged at ${formatTime(eventSeconds)}`,
                    );
                    button.classList.add("fired");
                    if (elements.tempInput) elements.tempInput.value = "";
                    notifyDisplayChange();
                } catch (error) {
                    console.error("Error:", error);
                    showToast("Error logging event. Please try again.", "error");
                } finally {
                    button.disabled = !state.isRunning;
                }
            });
        });
    }

    function wireManualEvent() {
        if (!elements.addEventBtn) return;
        elements.addEventBtn.addEventListener("click", async () => {
            const temperature = getUsableTemperature();
            const fan =
                document.getElementById("fan_setting").value ||
                state.lastFan ||
                0;
            const power =
                document.getElementById("power_setting").value ||
                state.lastPower ||
                0;
            const noteInput = document.getElementById("event_note");
            const note = noteInput.value || "";
            try {
                const response = await fetch(
                    `/api/roast/add_event/${config.roastId}`,
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            time_seconds: state.seconds,
                            temperature: temperature
                                ? parseInt(temperature, 10)
                                : null,
                            fan_setting: parseInt(fan, 10),
                            power_setting: parseInt(power, 10),
                            note,
                        }),
                    },
                );
                if (!response.ok) {
                    showMessage("Error logging data. Please try again.", "error");
                    return;
                }
                if (temperature) {
                    state.lastTemp = parseInt(temperature, 10);
                    state.lastTempIsStale = false;
                }
                state.lastFan = parseInt(fan, 10);
                state.lastPower = parseInt(power, 10);
                const emptyLog =
                    elements.timelineList.querySelector(".empty-log");
                if (emptyLog) emptyLog.remove();
                const item = document.createElement("div");
                item.className = "timeline-item timeline-temp";
                let content = temperature
                    ? `<span class="timeline-temp-value">${temperature}°C</span>`
                    : "";
                content +=
                    `<span class="timeline-settings">Fan: ${fan} | ` +
                    `Power: ${power}</span>`;
                if (note) {
                    content += `<span class="timeline-note">${note}</span>`;
                }
                item.innerHTML = `
                    <div class="timeline-time">${formatTime(state.seconds)}</div>
                    <div class="timeline-content">${content}</div>
                `;
                elements.timelineList.insertBefore(
                    item,
                    elements.timelineList.firstChild,
                );
                showMessage(`✓ Event logged at ${formatTime(state.seconds)}`);
                elements.tempInput.value = "";
                noteInput.value = "";
                notifyDisplayChange();
            } catch (error) {
                console.error("Error:", error);
                showToast("Error logging data. Please try again.", "error");
            }
        });
    }

    function switchTab(tabName) {
        document.querySelectorAll(".panel-tab").forEach((tab) => {
            tab.classList.toggle("active", tab.dataset.tab === tabName);
        });
        document.querySelectorAll(".tab-content").forEach((content) => {
            content.classList.remove("active");
        });
        const target = document.getElementById(
            tabName === "curve" ? "curveTabContent" : "logTabContent",
        );
        if (target) target.classList.add("active");
    }

    function boot() {
        wireSetupPersistence();
        wireCompleteDraft();
        wireStart();
        wireEnd();
        wireTimingEvents();
        wireManualEvent();
        if (config.roastEnded) return;

        if (config.roastStarted) {
            state.isRunning = true;
            if (elements.startBtn) elements.startBtn.style.display = "none";
            if (elements.endBtn) elements.endBtn.style.display = "inline-flex";
            elements.eventButtons.forEach((button) => {
                button.disabled = false;
            });
            if (elements.addEventBtn) elements.addEventBtn.disabled = false;
            document.getElementById("bean_id").disabled = true;
            document.getElementById("original_weight").disabled = true;
            collapseSetupOnStart();
            const fc = (config.keyTimings || []).findLast(
                timing => timing.event_name === "First Crack Start",
            );
            state.fcStartTime = fc ? fc.time_seconds : null;
            if (config.roastStartTime) {
                state.seconds = Math.floor(
                    (Date.now() - new Date(config.roastStartTime).getTime()) / 1000,
                );
                if (state.seconds < 0) state.seconds = 0;
                else if (state.seconds > 7200) {
                    console.warn(
                        "Calculated elapsed time exceeds 2 hours, may be stale data:",
                        state.seconds,
                    );
                }
                elements.timerDisplay.textContent = formatTime(state.seconds);
                state.timerInterval = setInterval(updateTimer, 1000);
            }
        }
        updateFcDisplay();
        startSyncLoop();
        chart.init();
        notifyDisplayChange();
    }

    return {
        state,
        elements,
        boot,
        adjustFan,
        adjustPower,
        toggleSetup,
        switchTab,
        setDisplayListener,
    };
}
