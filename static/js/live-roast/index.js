import { createChartController } from "./chart.js";
import { createFullscreenController } from "./fullscreen.js";
import { createSession, formatTime } from "./session.js";


const bootstrap = document.getElementById("live-roast-config");
const config = JSON.parse(bootstrap.textContent);
const chart = createChartController(formatTime);
const session = createSession(config, chart);
const fullscreen = createFullscreenController(session, chart);

window.adjustFan = session.adjustFan;
window.adjustPower = session.adjustPower;
window.toggleSetup = session.toggleSetup;
window.switchTab = session.switchTab;
window.toggleFullscreen = fullscreen.toggleFullscreen;
window.setCompactMode = fullscreen.setCompactMode;

function boot() {
    fullscreen.init();
    session.boot();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
} else {
    boot();
}
