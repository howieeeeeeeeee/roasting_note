/**
 * RoastChart - Shared chart component for roast visualization
 * Used by: roast_live.html, roast_detail.html, roast_edit.html
 */
const RoastChart = {
    chart: null,
    chartData: {
        labels: [],
        tempData: [],
        rorData: [],
        fanData: [],
        powerData: [],
        events: []
    },
    currentTempMax: 100,
    currentRoRMin: 0,
    currentMaxMinutes: 8,

    // Configuration
    config: {
        isLive: false,
        chartContainerId: 'roastCurveChart',
        powerCanvasId: 'powerTimeline',
        fanCanvasId: 'fanTimeline'
    },

    // Event colors for annotations
    eventColors: {
        'Yellowing': '#f0ad4e',
        'First Crack Start': '#d9534f',
        'First Crack End': '#c9302c',
        'Second Crack Start': '#5bc0de',
        'Second Crack End': '#31b0d5'
    },

    // Color palettes for power and fan segments (1-9 scale) - muted earth tones
    colorPalettes: {
        power: {
            1: '#F5F0EB', 2: '#E8DDD4', 3: '#D4C4B5',
            4: '#C0AB96', 5: '#A89282', 6: '#8F7A6A',
            7: '#7A6658', 8: '#6B5B4D', 9: '#5A4D42'
        },
        fan: {
            1: '#EDF3EE', 2: '#DAE7DC', 3: '#C4D9C7',
            4: '#ADCAB2', 5: '#96BA9C', 6: '#7FAA87',
            7: '#6B9A74', 8: '#6B8E6F', 9: '#5A7A5E'
        }
    },

    /**
     * Initialize the chart component
     * @param {Object} options - Configuration options
     */
    init(options = {}) {
        this.config = { ...this.config, ...options };
        this.resetData();
        this.initChart();
    },

    /**
     * Reset chart data
     */
    resetData() {
        this.chartData = {
            labels: [],
            tempData: [],
            rorData: [],
            fanData: [],
            powerData: [],
            events: []
        };
        this.currentTempMax = 100;
        this.currentRoRMin = 0;
        this.currentMaxMinutes = 8;
    },

    /**
     * Initialize Chart.js instance
     */
    initChart() {
        const canvas = document.getElementById(this.config.chartContainerId);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Temperature (\u00B0C)',
                        data: [],  // Will use {x, y} format
                        borderColor: '#6B5B4D',
                        backgroundColor: 'rgba(107, 91, 77, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        yAxisID: 'y-temp',
                        pointRadius: 0,
                        pointHoverRadius: 4
                    },
                    {
                        label: 'RoR (\u00B0C/min)',
                        data: [],  // Will use {x, y} format
                        borderColor: '#6B8E6F',
                        backgroundColor: 'rgba(107, 142, 111, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        yAxisID: 'y-ror',
                        pointRadius: 0,
                        pointHoverRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: {
                        type: 'linear',
                        title: {
                            display: true,
                            text: 'Time',
                            color: '#666'
                        },
                        min: 0,
                        ticks: {
                            color: '#666',
                            stepSize: 60,  // Show tick every 60 seconds
                            callback: function (value) {
                                // Format seconds to MM:SS (round to avoid floating point display)
                                const totalSeconds = Math.round(value);
                                const mins = Math.floor(totalSeconds / 60);
                                const secs = totalSeconds % 60;
                                return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    'y-temp': {
                        type: 'linear',
                        position: 'left',
                        min: 0,
                        max: this.currentTempMax,
                        title: {
                            display: true,
                            text: 'Temp (\u00B0C)',
                            color: '#6B5B4D'
                        },
                        ticks: {
                            color: '#6B5B4D',
                            stepSize: 25
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    'y-ror': {
                        type: 'linear',
                        position: 'right',
                        min: -10,  // Start with room for negative values
                        max: 30,   // Will expand dynamically
                        title: {
                            display: true,
                            text: 'RoR (\u00B0C/min)',
                            color: '#6B8E6F'
                        },
                        ticks: {
                            color: '#6B8E6F',
                            stepSize: 10
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            pointStyleWidth: 8,
                            boxHeight: 8,
                            padding: 12,
                            font: { size: 11 },
                            color: '#2C2C2C'
                        }
                    },
                    annotation: {
                        annotations: {}
                    },
                    tooltip: {
                        callbacks: {
                            title: function (context) {
                                // Format tooltip title as MM:SS
                                const seconds = Math.round(context[0].parsed.x);
                                const mins = Math.floor(seconds / 60);
                                const secs = seconds % 60;
                                return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
                            }
                        }
                    }
                },
                animation: this.config.isLive ? { duration: 0 } : {},
                layout: {
                    padding: {
                        top: 30  // Space for event marker labels
                    }
                }
            }
        });
    },

    /**
     * Initialize chart from existing data (for detail/edit pages)
     * @param {Array} tempCurve - Temperature curve data
     * @param {Array} keyTimings - Key timing events
     * @param {number} roastDuration - Optional total roast duration in seconds
     */
    initFromData(tempCurve, keyTimings = [], roastDuration = null) {
        if (!tempCurve || tempCurve.length === 0) return;

        // Track min/max for RoR
        let minRor = 0;
        let maxRor = 30;
        let maxTime = 0;

        // Populate chart data using {x, y} format
        tempCurve.forEach(entry => {
            const timeSeconds = entry.time_seconds;
            this.chartData.labels.push(timeSeconds);  // Store numeric seconds
            this.chartData.tempData.push(entry.temperature);

            // Filter RoR: only include if <= 30 (avoids spikes at beginning)
            const rorValue = (entry.ror !== null && entry.ror !== undefined && entry.ror <= 30) ? entry.ror : null;
            this.chartData.rorData.push(rorValue);
            this.chartData.fanData.push(entry.fan_setting || 0);
            this.chartData.powerData.push(entry.power_setting || 0);

            // Add to chart datasets using {x, y} format
            this.chart.data.datasets[0].data.push({ x: timeSeconds, y: entry.temperature });
            this.chart.data.datasets[1].data.push({ x: timeSeconds, y: rorValue });

            // Track max time
            if (timeSeconds > maxTime) maxTime = timeSeconds;

            // Track RoR range (only for valid values)
            if (rorValue !== null) {
                if (rorValue < minRor) minRor = Math.floor(rorValue / 10) * 10;
                if (rorValue > maxRor - 5) maxRor = Math.ceil(rorValue / 10) * 10 + 10;
            }
        });

        // Calculate dynamic Y-axis max for temperature
        const maxTemp = Math.max(...this.chartData.tempData);
        if (maxTemp > 180) this.currentTempMax = 230;
        else if (maxTemp > 150) this.currentTempMax = 190;
        else if (maxTemp > 120) this.currentTempMax = 160;
        else if (maxTemp > 90) this.currentTempMax = 130;
        else this.currentTempMax = 100;

        // Update chart scales
        if (this.chart) {
            // Set x-axis max: use roast duration if provided, otherwise use max data time
            let xAxisMax;
            if (roastDuration && roastDuration > 0) {
                // For finished roasts, use exact duration
                xAxisMax = roastDuration;
            } else {
                // Use max time from data
                xAxisMax = maxTime;
            }
            this.chart.options.scales.x.max = xAxisMax;

            // Set y-axis scales
            this.chart.options.scales['y-temp'].max = this.currentTempMax;
            this.chart.options.scales['y-ror'].min = minRor;
            this.chart.options.scales['y-ror'].max = maxRor;

            // Add event annotations
            keyTimings.forEach(timing => {
                this.addEventMarker(timing.time_seconds, timing.event_name);
            });

            this.chart.update('none');
        }

        // Draw timeline bars
        this.updatePFTimelines();
    },

    /**
     * Add a data point (for live roasting)
     * @param {number} timeSeconds - Time in seconds
     * @param {number} temp - Temperature
     * @param {number} ror - Rate of rise
     * @param {number} fan - Fan setting
     * @param {number} power - Power setting
     */
    addDataPoint(timeSeconds, temp, ror, fan, power) {
        if (!this.chart) return;

        const timeLabel = this.formatTime(timeSeconds);
        this.chartData.labels.push(timeLabel);
        this.chartData.tempData.push(temp);
        this.chartData.rorData.push(ror);

        // Fill empty fan/power with previous values
        const prevFan = this.chartData.fanData.length > 0
            ? this.chartData.fanData[this.chartData.fanData.length - 1]
            : 9;
        const prevPower = this.chartData.powerData.length > 0
            ? this.chartData.powerData[this.chartData.powerData.length - 1]
            : 3;

        this.chartData.fanData.push(fan || prevFan);
        this.chartData.powerData.push(power || prevPower);

        // Dynamically expand Y-axis
        this.updateYAxisScale(temp, ror);

        // Expand X-axis if needed
        const currentMinutes = timeSeconds / 60;
        if (currentMinutes > this.currentMaxMinutes - 1) {
            this.currentMaxMinutes += 2;
        }

        this.chart.update('none');
        this.updatePFTimelines();
    },

    /**
     * Update Y-axis scales based on data
     */
    updateYAxisScale(temp, ror) {
        if (!this.chart) return;

        // Temperature scale
        let newTempMax = this.currentTempMax;
        if (temp > 180 && this.currentTempMax < 230) newTempMax = 230;
        else if (temp > 150 && this.currentTempMax < 190) newTempMax = 190;
        else if (temp > 120 && this.currentTempMax < 160) newTempMax = 160;
        else if (temp > 90 && this.currentTempMax < 130) newTempMax = 130;

        if (newTempMax !== this.currentTempMax) {
            this.currentTempMax = newTempMax;
            this.chart.options.scales['y-temp'].max = newTempMax;
        }

        // RoR scale for negative values
        if (ror !== null && ror < this.currentRoRMin) {
            const newMin = Math.floor(ror / 10) * 10 - 10;
            this.currentRoRMin = newMin;
            this.chart.options.scales['y-ror'].min = newMin;
        }
    },

    /**
     * Add an event marker annotation
     * @param {number} timeSeconds - Time in seconds
     * @param {string} eventName - Event name
     */
    addEventMarker(timeSeconds, eventName) {
        if (!this.chart) return;

        const timeLabel = this.formatTime(timeSeconds);
        const color = this.eventColors[eventName] || '#6B5B4D';
        const annotationId = 'event-' + timeSeconds;

        if (!this.chart.options.plugins.annotation.annotations) {
            this.chart.options.plugins.annotation.annotations = {};
        }

        this.chart.options.plugins.annotation.annotations[annotationId] = {
            type: 'line',
            scaleID: 'x',
            value: timeSeconds,  // Use numeric seconds for linear x-axis
            borderColor: color,
            borderWidth: 2,
            borderDash: [5, 5],
            label: {
                display: true,
                content: eventName,
                position: 'start',
                backgroundColor: color,
                color: 'white',
                font: { size: 10, weight: 'bold' },
                padding: 4,
                yAdjust: 15  // Position inside chart area, below the top edge
            }
        };

        // Store event for reference
        this.chartData.events.push({
            time: timeSeconds,
            label: timeLabel,
            name: eventName,
            color: color
        });

        this.chart.update('none');
    },

    /**
     * Update Power/Fan timeline bars
     */
    updatePFTimelines() {
        const powerCanvas = document.getElementById(this.config.powerCanvasId);
        const fanCanvas = document.getElementById(this.config.fanCanvasId);

        if (powerCanvas) {
            this.drawSegmentedTimelineBar(powerCanvas, this.chartData.powerData, 'power', 'P');
        }
        if (fanCanvas) {
            this.drawSegmentedTimelineBar(fanCanvas, this.chartData.fanData, 'fan', 'F');
        }
    },

    /**
     * Detect segments where value changes
     * @param {Array} data - Array of values
     * @returns {Array} Segments with startIndex, endIndex, value
     */
    detectSegments(data) {
        const segments = [];
        if (data.length === 0) return segments;

        let currentSegment = { startIndex: 0, value: data[0] };

        for (let i = 1; i < data.length; i++) {
            if (data[i] !== currentSegment.value) {
                currentSegment.endIndex = i - 1;
                segments.push({ ...currentSegment });
                currentSegment = { startIndex: i, value: data[i] };
            }
        }

        // Close final segment
        currentSegment.endIndex = data.length - 1;
        segments.push(currentSegment);

        return segments;
    },

    /**
     * Draw segmented timeline bar with colors and labels
     * @param {HTMLCanvasElement} canvas - Canvas element
     * @param {Array} data - Array of values (1-9)
     * @param {string} type - 'power' or 'fan'
     * @param {string} labelPrefix - 'P' or 'F'
     */
    drawSegmentedTimelineBar(canvas, data, type, labelPrefix) {
        if (!canvas || data.length === 0) return;

        const ctx = canvas.getContext('2d');
        let width = canvas.getBoundingClientRect().width;
        if (width <= 0) {
            width = canvas.parentElement ? canvas.parentElement.offsetWidth - 50 : 300;
        }
        if (width <= 0) return;

        const height = 22;

        if (canvas.width !== width || canvas.height !== height) {
            canvas.width = width;
            canvas.height = height;
        }

        ctx.clearRect(0, 0, width, height);

        const segments = this.detectSegments(data);
        const totalPoints = data.length;
        const palette = this.colorPalettes[type];

        segments.forEach(segment => {
            const startX = (segment.startIndex / totalPoints) * width;
            const endX = ((segment.endIndex + 1) / totalPoints) * width;
            const segmentWidth = endX - startX;

            // Get color for value (clamp to 1-9)
            const value = Math.max(1, Math.min(9, segment.value || 1));
            const color = palette[value] || '#ccc';

            // Draw segment background
            ctx.fillStyle = color;
            ctx.fillRect(startX, 0, segmentWidth, height);

            // Draw segment border
            ctx.strokeStyle = 'rgba(0, 0, 0, 0.15)';
            ctx.lineWidth = 1;
            ctx.strokeRect(startX, 0, segmentWidth, height);

            // Draw label if segment is wide enough (> 20px)
            if (segmentWidth > 20) {
                // Text color based on background lightness
                ctx.fillStyle = value >= 5 ? '#fff' : '#333';
                ctx.font = 'bold 11px Inter, -apple-system, sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(`${labelPrefix}${value}`, startX + segmentWidth / 2, height / 2);
            }
        });
    },

    /**
     * Format seconds to MM:SS
     * @param {number} seconds - Time in seconds
     * @returns {string} Formatted time
     */
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    },

    /**
     * Get the chart instance
     * @returns {Chart} Chart.js instance
     */
    getChart() {
        return this.chart;
    },

    /**
     * Get chart data
     * @returns {Object} Chart data
     */
    getData() {
        return this.chartData;
    }
};
