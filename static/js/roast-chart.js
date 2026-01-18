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
    currentMaxMinutes: 8,

    // Configuration
    config: {
        isLive: false,
        chartContainerId: 'roastCurveChart'
    },

    // Event colors for annotations
    eventColors: {
        'Yellowing': '#f0ad4e',
        'First Crack Start': '#d9534f',
        'First Crack End': '#c9302c',
        'Second Crack Start': '#5bc0de',
        'Second Crack End': '#31b0d5',
        'Drop': '#8B4513'  // Saddle brown for drop event
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
                        pointHoverRadius: 4,
                        order: 1
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
                        pointHoverRadius: 4,
                        order: 2
                    },
                    {
                        label: 'Power',
                        data: [],
                        borderColor: 'rgba(139, 115, 85, 0.4)',
                        backgroundColor: 'rgba(139, 115, 85, 0.2)',
                        borderWidth: 1,
                        borderDash: [4, 3],
                        stepped: 'before',
                        fill: 'origin',
                        yAxisID: 'y-pf',
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        order: 10
                    },
                    {
                        label: 'Fan',
                        data: [],
                        borderColor: 'rgba(90, 122, 94, 0.4)',
                        backgroundColor: 'rgba(90, 122, 94, 0.2)',
                        borderWidth: 1,
                        borderDash: [4, 3],
                        stepped: 'before',
                        fill: 'origin',
                        yAxisID: 'y-pf',
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        order: 11
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
                        min: -10,
                        max: 40,
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
                    },
                    'y-pf': {
                        type: 'linear',
                        position: 'right',
                        min: 0,
                        max: 36,  // 9/36 = 25% of chart height
                        display: false,
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
                            color: '#2C2C2C',
                            filter: function(item) {
                                // Hide Power and Fan from legend
                                return !['Power', 'Fan'].includes(item.text);
                            }
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
                            },
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y;
                                if (label === 'Power') {
                                    return `Power: ${value}`;
                                }
                                if (label === 'Fan') {
                                    return `Fan: ${value}`;
                                }
                                if (label === 'RoR (\u00B0C/min)' && value !== null) {
                                    return `${label}: ${value.toFixed(1)}`;
                                }
                                return `${label}: ${value}`;
                            },
                            labelColor: function(context) {
                                const dataset = context.dataset || {};
                                const backgroundColor = dataset.backgroundColor || dataset.borderColor || '#999';
                                const borderColor = dataset.borderColor || backgroundColor;
                                return {
                                    borderColor: borderColor,
                                    backgroundColor: backgroundColor
                                };
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

        let maxTime = 0;

        // Populate chart data using {x, y} format
        tempCurve.forEach(entry => {
            const timeSeconds = entry.time_seconds;
            this.chartData.labels.push(timeSeconds);  // Store numeric seconds
            this.chartData.tempData.push(entry.temperature);

            // Filter RoR: only include if <= 30 (avoids spikes at beginning)
            const rorValue = (entry.ror !== null && entry.ror !== undefined && entry.ror <= 30) ? entry.ror : null;
            this.chartData.rorData.push(rorValue);
            const fanValue = entry.fan_setting || 0;
            const powerValue = entry.power_setting || 0;
            this.chartData.fanData.push(fanValue);
            this.chartData.powerData.push(powerValue);

            // Add to chart datasets using {x, y} format
            this.chart.data.datasets[0].data.push({ x: timeSeconds, y: entry.temperature });
            this.chart.data.datasets[1].data.push({ x: timeSeconds, y: rorValue });
            this.chart.data.datasets[2].data.push({ x: timeSeconds, y: powerValue });  // Power band
            this.chart.data.datasets[3].data.push({ x: timeSeconds, y: fanValue });    // Fan band

            // Track max time
            if (timeSeconds > maxTime) maxTime = timeSeconds;

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
            this.chart.options.scales['y-ror'].min = -10;
            this.chart.options.scales['y-ror'].max = 40;

            // Add event annotations
            keyTimings.forEach(timing => {
                this.addEventMarker(timing.time_seconds, timing.event_name);
            });

            this.chart.update('none');
        }
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

        const currentFan = fan || prevFan;
        const currentPower = power || prevPower;
        this.chartData.fanData.push(currentFan);
        this.chartData.powerData.push(currentPower);

        // Add to chart datasets
        this.chart.data.datasets[0].data.push({ x: timeSeconds, y: temp });
        this.chart.data.datasets[1].data.push({ x: timeSeconds, y: ror });
        this.chart.data.datasets[2].data.push({ x: timeSeconds, y: currentPower });  // Power band
        this.chart.data.datasets[3].data.push({ x: timeSeconds, y: currentFan });    // Fan band

        // Dynamically expand Y-axis
        this.updateYAxisScale(temp, ror);

        // Expand X-axis if needed
        const currentMinutes = timeSeconds / 60;
        if (currentMinutes > this.currentMaxMinutes - 1) {
            this.currentMaxMinutes += 2;
        }

        this.chart.update('none');
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
