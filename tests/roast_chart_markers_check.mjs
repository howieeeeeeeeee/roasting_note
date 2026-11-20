import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {createChartController} from '../static/js/live-roast/chart.js';
import {formatTime} from '../static/js/live-roast/session.js';

let renderedChart;
globalThis.document = {getElementById: () => ({getContext: () => ({})})};
globalThis.Chart = class {
    constructor(context, {options, data}) {
        this.options = options;
        this.data = data;
        renderedChart = this;
    }
    update() {}
};
// Live, edit and detail templates all load RoastChart as a classic script.
vm.runInThisContext(readFileSync(new URL('../static/js/roast-chart.js', import.meta.url), 'utf8'));

const firstCrack = 'First Crack Start';
const restored = [
    {event_name: firstCrack, time_seconds: 510},
    {event_name: 'Yellowing', time_seconds: 510},
    {event_name: firstCrack, time_seconds: 541},
    {event_name: 'First Crack End', time_seconds: 541},
];
const corrected = {event_name: firstCrack, time_seconds: 560};
function markers(name) {
    const annotations = Object.values(renderedChart.options.plugins.annotation.annotations);
    return annotations.filter(marker => marker.label.content === name).map(marker => marker.value);
}
function checkCorrection() {
    assert.deepEqual(markers(firstCrack), [560]);
    assert.deepEqual(markers('First Crack End'), [541]);
    assert.deepEqual(markers('Yellowing'), [510, 560]);
}

const live = createChartController(formatTime);
live.init(restored);
assert.deepEqual(markers(firstCrack), [541]);
assert.ok(renderedChart.options.scales.x.max >= 541);
live.addEventMarker(560, 'Yellowing');
live.addEventMarker(corrected.time_seconds, corrected.event_name);
checkCorrection();
// A correction beyond the current sensor samples must still be visible.
live.addEventMarker(905, firstCrack);
assert.deepEqual(markers(firstCrack), [905]);
assert.ok(renderedChart.options.scales.x.max >= 905);

RoastChart.init();
RoastChart.initFromData([{time_seconds: 600, temperature: 200}], [
    ...restored,
    {event_name: 'Yellowing', time_seconds: 560},
    corrected,
], 600);
checkCorrection();
