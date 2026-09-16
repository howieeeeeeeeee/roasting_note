const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const sandbox = {document: {getElementById: () => null}, console};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync('static/js/label-creator.js', 'utf8'), sandbox);
async function render(template, size) {
    const text = [];
    const ctx = new Proxy({
        fillText(value, x, y) { text.push({value, font: this.font, x, y}); },
        measureText(value) { return {width: value.length * parseFloat(this.font.split(' ')[1]) * 0.5}; },
        createLinearGradient() { return {addColorStop() {}}; },
        createRadialGradient() { return {addColorStop() {}}; },
    }, {get(target, key) { return key in target ? target[key] : () => {}; }});
    const canvas = {style: {}, getContext: () => ctx};
    sandbox.LabelCreator.renderLabel(canvas, template, {
        name: 'Coffee', origin: 'Ethiopia', process: 'Natural',
        flavorNotes: 'Berry\nCitrus', roastLevel: 'Light', roastDate: '2026-09-15',
    }, '#987654', '', 'craft', '5:4', size);
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(canvas.width, 2000);
    assert.equal(canvas.height, 1600);
    return text;
}
(async () => {
    for (const template of ['nova', 'ink', 'strip', 'washi']) {
        const normal = await render(template);
        assert(normal.length > 0);
        assert.deepEqual(await render(template, ''), normal);
        const fields = {
            name: value => value === 'Coffee',
            origin: value => value === 'ETHIOPIA',
            process: value => value === 'Natural' || value === 'NATURAL',
            roastLevel: value => value === 'Light',
            flavorNotes: value => ['Berry', 'Citrus', 'Berry, Citrus'].includes(value),
            roastDate: value => value.includes('2026-09-15'),
        };
        for (const [field, matches] of Object.entries(fields)) {
            assert.deepEqual(await render(template, {[field]: 999}), normal);
            for (const percent of [50, 125, 200]) {
                const scaled = await render(template, {[field]: percent});
                assert.equal(scaled.length, normal.length);
                assert(scaled.some(text => matches(text.value)));
                scaled.forEach((text, i) => {
                    const pixels = font => Number(font.match(/([\d.]+)px/)[1]);
                    assert.equal(text.value, normal[i].value);
                    const scale = matches(text.value) ? percent / 100 : 1;
                    assert(Math.abs(pixels(text.font) - pixels(normal[i].font) * scale) < 1e-8,
                        template + ': changing ' + field + ' affected ' + text.value);
                });
            }
        }
    }
})().catch(error => { console.error(error); process.exitCode = 1; });
