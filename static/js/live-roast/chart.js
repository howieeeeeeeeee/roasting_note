const EVENT_COLORS = {
    Yellowing: "#f0ad4e",
    "First Crack Start": "#d9534f",
    "First Crack End": "#c9302c",
    "Second Crack Start": "#5bc0de",
    "Second Crack End": "#31b0d5",
    Drop: "#8B4513",
};

export function createChartController(formatTime) {
    let chart = null;
    let currentMaxMinutes = 8;
    let currentTempMax = 100;
    const chartData = {
        labels: [],
        tempData: [],
        rorData: [],
        fanData: [],
        powerData: [],
        events: [],
    };

    function init() {
        const canvas = document.getElementById("roastCurveChart");
        if (!canvas) return;
        chart = new Chart(canvas.getContext("2d"), {
            type: "line",
            data: {
                datasets: [
                    {
                        label: "Temperature (°C)",
                        data: [],
                        borderColor: "#6B5B4D",
                        backgroundColor: "rgba(107, 91, 77, 0.1)",
                        borderWidth: 2,
                        tension: 0.3,
                        yAxisID: "y-temp",
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        order: 1,
                    },
                    {
                        label: "RoR (°C/min)",
                        data: [],
                        borderColor: "#6B8E6F",
                        backgroundColor: "rgba(107, 142, 111, 0.1)",
                        borderWidth: 2,
                        tension: 0.3,
                        yAxisID: "y-ror",
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        order: 2,
                    },
                    {
                        label: "Power",
                        data: [],
                        borderColor: "rgba(139, 115, 85, 0.4)",
                        backgroundColor: "rgba(139, 115, 85, 0.2)",
                        borderWidth: 1,
                        borderDash: [4, 3],
                        stepped: "before",
                        fill: "origin",
                        yAxisID: "y-pf",
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        order: 10,
                    },
                    {
                        label: "Fan",
                        data: [],
                        borderColor: "rgba(90, 122, 94, 0.4)",
                        backgroundColor: "rgba(90, 122, 94, 0.2)",
                        borderWidth: 1,
                        borderDash: [4, 3],
                        stepped: "before",
                        fill: "origin",
                        yAxisID: "y-pf",
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        order: 11,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: "index", intersect: false },
                scales: {
                    x: {
                        type: "linear",
                        title: { display: true, text: "Time", color: "#666" },
                        min: 0,
                        max: currentMaxMinutes * 60,
                        ticks: {
                            color: "#666",
                            stepSize: 60,
                            callback(value) {
                                return formatTime(value);
                            },
                        },
                        grid: { color: "rgba(0, 0, 0, 0.05)" },
                    },
                    "y-temp": {
                        type: "linear",
                        position: "left",
                        min: 0,
                        max: 100,
                        title: {
                            display: true,
                            text: "Temp (°C)",
                            color: "#6B5B4D",
                        },
                        ticks: { color: "#6B5B4D", stepSize: 25 },
                        grid: { color: "rgba(0, 0, 0, 0.05)" },
                    },
                    "y-ror": {
                        type: "linear",
                        position: "right",
                        min: -10,
                        max: 40,
                        title: {
                            display: true,
                            text: "RoR (°C/min)",
                            color: "#6B8E6F",
                        },
                        ticks: { color: "#6B8E6F", stepSize: 10 },
                        grid: { drawOnChartArea: false },
                    },
                    "y-pf": {
                        type: "linear",
                        position: "right",
                        min: 0,
                        max: 36,
                        display: false,
                        grid: { drawOnChartArea: false },
                    },
                },
                plugins: {
                    legend: {
                        position: "top",
                        labels: {
                            usePointStyle: true,
                            pointStyleWidth: 8,
                            boxHeight: 8,
                            padding: 12,
                            font: { size: 11 },
                            color: "#2C2C2C",
                            filter(item) {
                                return !["Power", "Fan"].includes(item.text);
                            },
                        },
                    },
                    annotation: { annotations: {} },
                    tooltip: {
                        callbacks: {
                            title(context) {
                                return formatTime(context[0].parsed.x);
                            },
                            label(context) {
                                const label = context.dataset.label || "";
                                const value = context.parsed.y;
                                if (label === "Power" || label === "Fan") {
                                    return `${label}: ${value}`;
                                }
                                if (label === "RoR (°C/min)" && value !== null) {
                                    return `${label}: ${value.toFixed(1)}`;
                                }
                                return `${label}: ${value}`;
                            },
                            labelColor(context) {
                                const dataset = context.dataset || {};
                                const backgroundColor =
                                    dataset.backgroundColor ||
                                    dataset.borderColor ||
                                    "#999";
                                return {
                                    borderColor: dataset.borderColor || backgroundColor,
                                    backgroundColor,
                                };
                            },
                        },
                    },
                },
                animation: { duration: 0 },
                layout: { padding: { top: 30 } },
            },
        });
    }

    function updateScales(temperature) {
        let newMaximum = currentTempMax;
        if (temperature > 180) newMaximum = 230;
        else if (temperature > 150) newMaximum = 190;
        else if (temperature > 120) newMaximum = 160;
        else if (temperature > 90) newMaximum = 130;
        if (newMaximum > currentTempMax) {
            currentTempMax = newMaximum;
            chart.options.scales["y-temp"].max = currentTempMax;
        }
    }

    function updateData(timeSeconds, temperature, ror, fan, power) {
        if (!chart) return;
        const lastFan =
            chartData.fanData.at(-1) === undefined ? 9 : chartData.fanData.at(-1);
        const lastPower =
            chartData.powerData.at(-1) === undefined
                ? 3
                : chartData.powerData.at(-1);
        const currentFan = fan !== null ? fan : lastFan;
        const currentPower = power !== null ? power : lastPower;
        const filteredRor = ror !== null && ror !== undefined && ror <= 30 ? ror : null;

        chartData.labels.push(timeSeconds);
        chartData.tempData.push(temperature);
        chartData.rorData.push(ror);
        chartData.fanData.push(currentFan);
        chartData.powerData.push(currentPower);
        chart.data.datasets[0].data.push({ x: timeSeconds, y: temperature });
        chart.data.datasets[1].data.push({ x: timeSeconds, y: filteredRor });
        chart.data.datasets[2].data.push({ x: timeSeconds, y: currentPower });
        chart.data.datasets[3].data.push({ x: timeSeconds, y: currentFan });
        updateScales(temperature);

        const currentMinutes = timeSeconds / 60;
        if (currentMinutes > currentMaxMinutes - 1) {
            currentMaxMinutes = Math.ceil(currentMinutes / 2) * 2 + 2;
            chart.options.scales.x.max = currentMaxMinutes * 60;
        }
        chart.update("none");
    }

    function addEventMarker(timeSeconds, eventName) {
        if (!chart) return;
        const color = EVENT_COLORS[eventName] || "#6B5B4D";
        const annotationId = `event-${timeSeconds}`;
        chart.options.plugins.annotation.annotations[annotationId] = {
            type: "line",
            scaleID: "x",
            value: timeSeconds,
            borderColor: color,
            borderWidth: 2,
            borderDash: [5, 5],
            label: {
                display: true,
                content: eventName,
                position: "start",
                backgroundColor: color,
                color: "white",
                font: { size: 10, weight: "bold" },
                padding: 4,
                yAdjust: 15,
            },
        };
        chartData.events.push({
            time: timeSeconds,
            label: formatTime(timeSeconds),
            name: eventName,
            color,
        });
        chart.update();
    }

    function resize(delay = 0) {
        setTimeout(() => {
            if (chart) chart.resize();
        }, delay);
    }

    return { init, updateData, addEventMarker, resize };
}
