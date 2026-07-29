export function createFullscreenController(session, chart) {
    const { elements, state } = session;
    const controls = {
        startBtn: document.getElementById("fsStartBtn"),
        endBtn: document.getElementById("fsEndBtn"),
        bar: document.getElementById("fsControlsBar"),
        temperature: document.getElementById("fsTemperature"),
        fanValue: document.getElementById("fsFanValue"),
        powerValue: document.getElementById("fsPowerValue"),
        eventNote: document.getElementById("fsEventNote"),
        logEventBtn: document.getElementById("fsLogEventBtn"),
        eventButtons: document.querySelectorAll(".fs-event-btn"),
    };
    let isFullscreen = false;
    let isCompactMode = false;

    function syncDisplays() {
        if (!isFullscreen) return;
        const timer = document.getElementById("fsTimerDisplay");
        if (timer) timer.textContent = elements.timerDisplay.textContent;

        const fsFcTime = document.getElementById("fsFcTimeDisplay");
        const fcTime = document.getElementById("fcTimeDisplay");
        if (fsFcTime && fcTime) {
            fsFcTime.textContent = fcTime.textContent;
            fsFcTime.style.display = fcTime.style.display;
        }

        const temperature = document.getElementById("fsTempValue");
        if (temperature && elements.tempValueDisplay) {
            temperature.textContent = elements.tempValueDisplay.textContent;
            temperature.style.color = elements.tempValueDisplay.style.color;
        }
        const status = document.getElementById("fsTempSensorStatus");
        if (status && elements.tempSensorStatus) {
            status.textContent = elements.tempSensorStatus.textContent;
            status.className =
                `fs-sensor-status ` +
                elements.tempSensorStatus.className.replace("tb-sub ", "");
        }
        const ror = document.getElementById("fsRorValue");
        if (ror && elements.rorDisplay) {
            ror.textContent = elements.rorDisplay.textContent;
        }
    }

    function syncButtons() {
        if (controls.startBtn && elements.startBtn) {
            controls.startBtn.style.display =
                elements.startBtn.style.display === "none"
                    ? "none"
                    : "inline-flex";
        }
        if (controls.endBtn && elements.endBtn) {
            controls.endBtn.style.display =
                elements.endBtn.style.display === "none"
                    ? "none"
                    : "inline-flex";
        }
    }

    function syncControlsBar() {
        if (controls.fanValue) {
            controls.fanValue.textContent =
                document.getElementById("fanValue").textContent;
        }
        if (controls.powerValue) {
            controls.powerValue.textContent =
                document.getElementById("powerValue").textContent;
        }
        if (controls.temperature) {
            controls.temperature.value =
                document.getElementById("temperature").value || "";
        }
        if (controls.eventNote) {
            controls.eventNote.value =
                document.getElementById("event_note").value || "";
        }
        controls.eventButtons.forEach((button, index) => {
            if (elements.eventButtons[index]) {
                button.disabled = elements.eventButtons[index].disabled;
            }
        });
        if (controls.logEventBtn && elements.addEventBtn) {
            controls.logEventBtn.disabled = elements.addEventBtn.disabled;
        }
    }

    function handleOrientationChange() {
        if (!isFullscreen) return;
        const container = document.getElementById("liveRoastContainer");
        const landscape = window.innerWidth > window.innerHeight;
        container.classList.toggle("fullscreen-landscape", landscape);
        container.classList.toggle("fullscreen-portrait", !landscape);
        chart.resize(150);
    }

    function toggleFullscreen() {
        isFullscreen = !isFullscreen;
        const body = document.body;
        const container = document.getElementById("liveRoastContainer");
        const pageHeader = document.getElementById("pageHeader");
        const fullscreenBtn = document.getElementById("fullscreenBtn");
        const exitBtn = document.getElementById("exitFullscreenBtn");
        const readings = document.getElementById("fullscreenReadings");
        const setup = document.getElementById("setupSection");
        const navbar = document.querySelector(".navbar");
        const footer = document.querySelector("footer");
        const main = document.querySelector(".container");

        if (isFullscreen) {
            body.classList.add("fullscreen-mode");
            container.classList.add("fullscreen-active");
            pageHeader.style.display = "none";
            fullscreenBtn.style.display = "none";
            exitBtn.style.display = "flex";
            readings.style.display = "flex";
            setup.style.display = "none";
            if (navbar) navbar.style.display = "none";
            if (footer) footer.style.display = "none";
            if (main) main.classList.add("fullscreen-container");
            syncDisplays();
            syncButtons();
            handleOrientationChange();
            chart.resize(150);
            return;
        }

        body.classList.remove("fullscreen-mode");
        container.classList.remove(
            "fullscreen-active",
            "fullscreen-landscape",
            "fullscreen-portrait",
            "fullscreen-compact",
        );
        pageHeader.style.display = "flex";
        fullscreenBtn.style.display = "inline-flex";
        exitBtn.style.display = "none";
        readings.style.display = "none";
        if (controls.bar) controls.bar.style.display = "none";
        setup.style.display = "block";
        if (navbar) navbar.style.display = "block";
        if (footer) footer.style.display = "block";
        if (main) main.classList.remove("fullscreen-container");
        const leftPanel = document.getElementById("leftPanel");
        if (leftPanel) leftPanel.style.width = "";
        isCompactMode = false;
        chart.resize(150);
    }

    function setCompactMode(compact) {
        isCompactMode = compact;
        const container = document.getElementById("liveRoastContainer");
        container.classList.toggle("fullscreen-compact", compact);
        if (compact) syncControlsBar();
    }

    function wireControls() {
        if (controls.startBtn) {
            controls.startBtn.addEventListener("click", () => {
                elements.startBtn.click();
            });
        }
        if (controls.endBtn) {
            controls.endBtn.addEventListener("click", () => {
                elements.endBtn.click();
            });
        }
        if (controls.temperature) {
            controls.temperature.addEventListener("input", () => {
                document.getElementById("temperature").value =
                    controls.temperature.value;
            });
        }
        if (controls.eventNote) {
            controls.eventNote.addEventListener("input", () => {
                document.getElementById("event_note").value =
                    controls.eventNote.value;
            });
        }
        controls.eventButtons.forEach((button, index) => {
            button.addEventListener("click", () => {
                if (elements.eventButtons[index]) {
                    elements.eventButtons[index].click();
                }
            });
        });
        if (controls.logEventBtn) {
            controls.logEventBtn.addEventListener("click", () => {
                elements.addEventBtn.click();
            });
        }
    }

    function wireResizeHandle() {
        const resizeHandle = document.getElementById("resizeHandle");
        const leftPanel = document.getElementById("leftPanel");
        if (!resizeHandle || !leftPanel) return;
        const compactThreshold = 100;
        let resizing = false;
        let startX = 0;
        let startWidth = 0;

        function stopResize() {
            resizing = false;
            resizeHandle.classList.remove("dragging");
            document.removeEventListener("mousemove", doResize);
            document.removeEventListener("mouseup", stopResize);
            document.removeEventListener("touchmove", doResize);
            document.removeEventListener("touchend", stopResize);
            chart.resize(50);
        }

        function doResize(event) {
            if (!resizing) return;
            const clientX =
                event.type === "touchmove"
                    ? event.touches[0].clientX
                    : event.clientX;
            const newWidth = startWidth + clientX - startX;
            if (newWidth < compactThreshold) {
                setCompactMode(true);
                stopResize();
                return;
            }
            const maximum = window.innerWidth * 0.5;
            if (newWidth >= 280 && newWidth <= maximum) {
                leftPanel.style.width = `${newWidth}px`;
            }
            event.preventDefault();
        }

        function startResize(event) {
            if (!isFullscreen || isCompactMode) return;
            resizing = true;
            resizeHandle.classList.add("dragging");
            startX =
                event.type === "touchstart"
                    ? event.touches[0].clientX
                    : event.clientX;
            startWidth = leftPanel.offsetWidth;
            document.addEventListener("mousemove", doResize);
            document.addEventListener("mouseup", stopResize);
            document.addEventListener("touchmove", doResize, { passive: false });
            document.addEventListener("touchend", stopResize);
            event.preventDefault();
        }

        resizeHandle.addEventListener("mousedown", startResize);
        resizeHandle.addEventListener("touchstart", startResize, {
            passive: false,
        });
    }

    function init() {
        wireControls();
        wireResizeHandle();
        window.addEventListener("resize", handleOrientationChange);
        window.addEventListener("orientationchange", handleOrientationChange);
        const observer = new MutationObserver(() => {
            if (isFullscreen) syncButtons();
        });
        if (elements.startBtn) {
            observer.observe(elements.startBtn, {
                attributes: true,
                attributeFilter: ["style"],
            });
        }
        if (elements.endBtn) {
            observer.observe(elements.endBtn, {
                attributes: true,
                attributeFilter: ["style"],
            });
        }
        session.setDisplayListener(() => {
            if (isFullscreen) {
                syncDisplays();
                syncButtons();
                if (isCompactMode) syncControlsBar();
            }
        });
    }

    return { init, toggleFullscreen, setCompactMode };
}
