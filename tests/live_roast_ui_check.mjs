import assert from 'node:assert/strict';
import {createSession, defaultRoastTitle} from '../static/js/live-roast/session.js';
import {createFullscreenController} from '../static/js/live-roast/fullscreen.js';

for (const title of ['', ' Untitled ', 'uNtItLeD rOaSt']) {
    assert.equal(defaultRoastTitle(title, ' Guji  Hambela Bishan Wate '), 'Bishan Wate');
    assert.equal(defaultRoastTitle(title, 'Central Valley Volcan Azul Alejo Castro Reserve Villa Sarchi'), 'Villa Sarchi');
    assert.equal(defaultRoastTitle(title, 'Solo'), 'Solo');
    assert.equal(defaultRoastTitle(title, ''), title);
}
assert.equal(defaultRoastTitle('My custom title', 'Other Bean'), 'My custom title');
assert.equal(defaultRoastTitle('Bishan Wate', 'Other Bean'), 'Bishan Wate');

class Element {
    value = ''; textContent = ''; className = '';  style = {}; disabled = false; dataset = {};
    listeners = {}; classList = {add(){}, remove(){}, toggle(){}};
    addEventListener(event, action) { (this.listeners[event] ||= []).push(action); }
    querySelector() { return null; }
    insertBefore() {}
    async fire(event) { for (const action of this.listeners[event] || []) await action(); }
}
let ids, eventButton, tick, requests, reply, pendingSave;
function environment() {
    ids = new Map(); requests = []; pendingSave = null;
    const get = id => { if (!ids.has(id)) ids.set(id, new Element()); return ids.get(id); };
    eventButton = new Element(); eventButton.dataset.event = 'First Crack Start';
    get('bean_id').value = 'bean-id';
    get('bean_id').selectedOptions = [{dataset: {beanName: 'Guji Hambela Bishan Wate'}}];
    get('original_weight').value = '200';
    get('roast_title').value = 'Untitled Roast';
    get('fan_setting').value = '9'; get('power_setting').value = '3';
    globalThis.document = {
        getElementById: get,
        querySelectorAll: selector => selector === '.event-btn-compact' ? [eventButton] : [],
        querySelector: () => new Element(), createElement: () => new Element(), body: new Element(),
    };
    globalThis.window = {addEventListener(){}, location: {}, innerWidth:1024, innerHeight:768};
    globalThis.showToast = () => {};
    globalThis.MutationObserver = class {observe(){}};
    globalThis.setInterval = fn => {tick = fn; return 1;};
    globalThis.clearInterval = () => {tick = null;};
    globalThis.setTimeout = () => 1;
    globalThis.clearTimeout = () => {};
    reply = {ok:true, success:true};
    globalThis.fetch = async (url, options) => {
        requests.push({url, data:JSON.parse(options.body)});
        if (url.includes('update_setup') && pendingSave) await pendingSave;
        const response = url.includes('add_timing') ? {...reply} : {ok:true, success:true};
        return {ok:response.ok, json:async()=>({...response, temperature:null})};
    };
}
const chart = {init(){}, updateData(){}, addEventMarker(){}, resize(){}};
// Resuming uses persisted timing and the same clock for normal/fullscreen.
environment();
let session = createSession({roastId:'r', roastStarted:true,
    roastStartTime:new Date(Date.now()-90000).toISOString(),
    keyTimings:[{event_name:'First Crack Start',time_seconds:60}]}, chart);
session.boot();
assert.equal(session.state.fcStartTime,60);
assert.equal(ids.get('fcElapsedValue').textContent,'00:30');
let fullscreen = createFullscreenController(session,chart); fullscreen.init(); fullscreen.toggleFullscreen();
assert.equal(ids.get('fsFcTimeDisplay').textContent,'Since FC 00:30');
tick(); assert.equal(ids.get('fcElapsedValue').textContent,'00:31');
assert.equal(ids.get('fsFcTimeDisplay').textContent,'Since FC 00:31');
fullscreen.toggleFullscreen(); tick(); fullscreen.toggleFullscreen();
assert.equal(ids.get('fsFcTimeDisplay').textContent,'Since FC 00:32');
// HTTP and application-level failures preserve the saved origin.
for (const failure of [{ok:false,success:false},{ok:true,success:false}]) {
    reply = failure; await eventButton.fire('click'); assert.equal(session.state.fcStartTime,60);
}
reply = {ok:true,success:true}; await eventButton.fire('click');
assert.equal(session.state.fcStartTime,92);
assert.equal(ids.get('fcElapsedValue').textContent,'00:00');
await ids.get('endBtn').fire('click'); assert.equal(tick,null);
// Draft selection fills before autosave, serializes pending writes, and start waits.
environment(); session = createSession({roastId:'draft'},chart); session.boot();
fullscreen = createFullscreenController(session,chart); fullscreen.init(); fullscreen.toggleFullscreen();
assert.equal(ids.get('fsFcTimeDisplay').style.display,'none');
await ids.get('bean_id').fire('input');
assert.equal(ids.get('roast_title').value,'Bishan Wate');
let release; pendingSave = new Promise(resolve => {release=resolve;});
const start = ids.get('startBtn').fire('click');
await Promise.resolve(); await Promise.resolve();
assert.equal(requests.filter(r=>r.url.includes('/start/')).length,0);
release(); await start;
assert.equal(requests.find(r=>r.url.includes('update_setup')).data.title,'Bishan Wate');
assert.equal(requests.filter(r=>r.url.includes('/start/')).length,1);
assert.equal(session.state.isRunning,true);
// A failed FC from a fresh roast must not invent an origin.
reply={ok:false,success:false}; await eventButton.fire('click');
assert.equal(session.state.fcStartTime,null);
console.log('Live UI behavior passed');
