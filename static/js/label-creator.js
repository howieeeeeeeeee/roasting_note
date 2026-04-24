/**
 * label-creator.js — RoastLogger Bean Label System
 * Templates: nova, ink, strip, washi
 * Font presets: modern, editorial, technical, bold, craft
 * Aspect ratios: 2:1, 5:3, 5:4, 4:3, 3:4
 */
var LabelCreator = (function () {

    var RENDER_SCALE = 4;

    // ── Font Presets ─────────────────────────────────────────────────
    var FONT_PRESETS = {
        modern:    { name: 'Raleway',          nameW: 800, body: 'Inter',       bodyW: 400, label: 'Modern'    },
        editorial: { name: 'Playfair Display',  nameW: 700, body: 'Inter',       bodyW: 400, label: 'Editorial' },
        technical: { name: 'DM Mono',           nameW: 500, body: 'DM Mono',     bodyW: 400, label: 'Technical' },
        bold:      { name: 'Barlow Condensed',  nameW: 800, body: 'Inter',       bodyW: 400, label: 'Bold'      },
        craft:     { name: 'Roboto Slab',       nameW: 700, body: 'Roboto Slab', bodyW: 400, label: 'Craft'     },
    };

    // ── Aspect Ratios ────────────────────────────────────────────────
    var ASPECT_RATIOS = {
        '2:1': [2, 1],
        '5:3': [5, 3],
        '5:4': [5, 4],
        '4:3': [4, 3],
        '3:4': [3, 4],
    };

    // ── Template Definitions ─────────────────────────────────────────
    // Each template is a render function signature; actual drawing is in renderLabel()
    var TEMPLATES = {
        nova: {
            id: 'nova',
            name: 'Nova',
            description: 'Split layout — text left, image right',
            defaultRatio: '5:4',
            exportWidthCm: 10,
            exportHeightCm: 8,
        },
        ink: {
            id: 'ink',
            name: 'Ink',
            description: 'Dark background, full-bleed',
            defaultRatio: '5:4',
            exportWidthCm: 10,
            exportHeightCm: 8,
        },
        strip: {
            id: 'strip',
            name: 'Strip',
            description: 'Minimal Swiss grid, accent band',
            defaultRatio: '5:4',
            exportWidthCm: 10,
            exportHeightCm: 8,
        },
        washi: {
            id: 'washi',
            name: 'Washi',
            description: 'Craft paper, centred layout',
            defaultRatio: '5:4',
            exportWidthCm: 10,
            exportHeightCm: 8,
        },
    };

    // ── Image cache ──────────────────────────────────────────────────
    var imageCache = {};

    function loadImage(src) {
        if (!src) return Promise.resolve(null);
        if (imageCache[src]) return Promise.resolve(imageCache[src]);
        return new Promise(function (resolve) {
            var img = new Image();
            img.crossOrigin = 'anonymous';
            img.onload  = function () { imageCache[src] = img; resolve(img); };
            img.onerror = function () { resolve(null); };
            img.src = src;
        });
    }

    function getTemplate(id) {
        return TEMPLATES[id] || TEMPLATES.nova;
    }

    // ── Canvas helpers ───────────────────────────────────────────────
    function roundRect(ctx, x, y, w, h, r, fillStyle) {
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + w - r, y);
        ctx.arcTo(x + w, y, x + w, y + r, r);
        ctx.lineTo(x + w, y + h - r);
        ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
        ctx.lineTo(x + r, y + h);
        ctx.arcTo(x, y + h, x, y + h - r, r);
        ctx.lineTo(x, y + r);
        ctx.arcTo(x, y, x + r, y, r);
        ctx.closePath();
        if (fillStyle) { ctx.fillStyle = fillStyle; ctx.fill(); }
    }

    function txt(ctx, str, x, y, font, color, align, baseline) {
        if (!str) return;
        ctx.font      = font;
        ctx.fillStyle = color;
        ctx.textAlign = align    || 'left';
        ctx.textBaseline = baseline || 'alphabetic';
        ctx.fillText(str, x, y);
    }

    function nameFontStr(preset, sz) {
        var f = FONT_PRESETS[preset] || FONT_PRESETS.modern;
        return f.nameW + ' ' + sz + "px '" + f.name + "', sans-serif";
    }

    function bodyFontStr(preset, sz, weight) {
        var f = FONT_PRESETS[preset] || FONT_PRESETS.modern;
        return (weight || f.bodyW) + ' ' + sz + "px '" + f.body + "', sans-serif";
    }

    // Draw contain-fit image into a rectangular area
    function drawImageContain(ctx, img, areaX, areaY, areaW, areaH) {
        if (!img) return;
        var imgAspect  = img.naturalWidth / img.naturalHeight;
        var areaAspect = areaW / areaH;
        var dw, dh;
        if (imgAspect > areaAspect) { dw = areaW; dh = dw / imgAspect; }
        else                        { dh = areaH; dw = dh * imgAspect; }
        ctx.drawImage(img, areaX + (areaW - dw) / 2, areaY + (areaH - dh) / 2, dw, dh);
    }

    // ── Main render ──────────────────────────────────────────────────
    /**
     * @param {HTMLCanvasElement} canvas
     * @param {string} templateId   — 'nova' | 'ink' | 'strip' | 'washi'
     * @param {Object} fields       — { name, origin, process, roastLevel, flavorNotes, roastDate }
     * @param {string} accentColor  — hex e.g. '#9B6A6A'
     * @param {string} imageSrc     — URL or '' (for nova: right panel; for ink/washi: bg)
     * @param {string} fontPreset   — key from FONT_PRESETS
     * @param {string} aspectRatio  — key from ASPECT_RATIOS e.g. '5:4'
     */
    function renderLabel(canvas, templateId, fields, accentColor, imageSrc, fontPreset, aspectRatio) {
        var preset  = fontPreset  || 'modern';
        var ratioKey = aspectRatio || '5:4';
        var ratio    = ASPECT_RATIOS[ratioKey] || [5, 4];
        var accent   = accentColor || '#9B6A6A';

        var BASE_W = 500;
        var w = BASE_W;
        var h = Math.round(w * ratio[1] / ratio[0]);

        canvas.width  = w * RENDER_SCALE;
        canvas.height = h * RENDER_SCALE;
        canvas.style.width  = w + 'px';
        canvas.style.height = h + 'px';

        var ctx = canvas.getContext('2d');
        ctx.scale(RENDER_SCALE, RENDER_SCALE);
        ctx.clearRect(0, 0, w, h);

        var img = imageSrc ? imageCache[imageSrc] : null;

        switch (templateId) {
            case 'ink':   renderInk(ctx, w, h, fields, accent, img, preset);   break;
            case 'strip': renderStrip(ctx, w, h, fields, accent, img, preset); break;
            case 'washi': renderWashi(ctx, w, h, fields, accent, img, preset); break;
            default:      renderNova(ctx, w, h, fields, accent, img, preset);  break;
        }

        // Update export px display if element present
        var infoEl = document.getElementById('labelExportInfo');
        if (infoEl) infoEl.textContent = canvas.width + ' × ' + canvas.height;
    }

    // ════════════════════════════════════════════════════
    // T1 — Nova (split left-text / right-image)
    // ════════════════════════════════════════════════════
    function renderNova(ctx, w, h, f, accent, img, preset) {
        var isPortrait = h > w * 0.9;

        // White bg
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, w, h);
        ctx.strokeStyle = '#EBEBEB'; ctx.lineWidth = 0.5;
        ctx.strokeRect(0.25, 0.25, w - 0.5, h - 0.5);

        // Image panel
        var imgX = isPortrait ? 0    : w * 0.5;
        var imgY = isPortrait ? h * 0.5 : 0;
        var imgW = isPortrait ? w    : w * 0.5;
        var imgH = isPortrait ? h * 0.5 : h;

        if (img) {
            // Clip to right panel
            ctx.save();
            ctx.beginPath();
            ctx.rect(imgX, imgY, imgW, imgH);
            ctx.clip();
            drawImageContain(ctx, img, imgX + imgW * 0.05, imgY + imgH * 0.05, imgW * 0.9, imgH * 0.9);
            ctx.restore();
        } else {
            // Warm gradient fallback with silhouette
            var grd = ctx.createLinearGradient(imgX, imgY, imgX + imgW, imgY + imgH);
            grd.addColorStop(0, '#F0EDE8'); grd.addColorStop(1, '#E4DDD4');
            ctx.fillStyle = grd; ctx.fillRect(imgX, imgY, imgW, imgH);
            // Silhouette
            ctx.save(); ctx.globalAlpha = 0.18; ctx.fillStyle = '#6A5548';
            ctx.beginPath(); ctx.ellipse(imgX + imgW * 0.5, imgY + imgH * 0.64, imgW * 0.24, imgH * 0.30, 0, 0, Math.PI * 2); ctx.fill();
            ctx.beginPath(); ctx.ellipse(imgX + imgW * 0.5, imgY + imgH * 0.26, imgW * 0.16, imgH * 0.15, 0, 0, Math.PI * 2); ctx.fill();
            ctx.strokeStyle = '#6A5548'; ctx.lineWidth = imgW * 0.025; ctx.lineCap = 'round';
            ctx.beginPath();
            ctx.moveTo(imgX + imgW * 0.68, imgY + imgH * 0.82);
            ctx.quadraticCurveTo(imgX + imgW * 0.82, imgY + imgH * 0.70, imgX + imgW * 0.76, imgY + imgH * 0.55);
            ctx.stroke();
            ctx.globalAlpha = 1; ctx.restore();
        }

        // Dashed centre divider
        ctx.save(); ctx.setLineDash([3, 5]); ctx.strokeStyle = '#D0CBC5'; ctx.lineWidth = 0.75;
        ctx.beginPath();
        if (isPortrait) { ctx.moveTo(w * 0.04, h * 0.5); ctx.lineTo(w * 0.96, h * 0.5); }
        else            { ctx.moveTo(w * 0.5, h * 0.03); ctx.lineTo(w * 0.5, h * 0.97); }
        ctx.stroke(); ctx.setLineDash([]); ctx.restore();

        // Accent bar
        var barW = Math.max(4, w * 0.010);
        var barX = 12, barY = h * 0.08, barH = h * 0.62;
        roundRect(ctx, barX, barY, barW, barH, barW / 2, accent);

        // Text area
        var textW = isPortrait ? w : w * 0.5;
        var tx     = 26;
        var nameSz = Math.max(20, Math.min(40, textW * 0.17));
        var subSz  = Math.max(10, Math.min(15, textW * 0.048));
        var bodySz = Math.max(8,  Math.min(12, textW * 0.034));

        // Name — auto-wrap to 2 lines if needed
        ctx.font = nameFontStr(preset, nameSz);
        var maxNameW   = textW - tx - 14;
        var nameWords  = (f.name || '').split(' ');
        var line1 = '', line2 = '', testLine = '';
        for (var wi = 0; wi < nameWords.length; wi++) {
            var tryLine = testLine ? testLine + ' ' + nameWords[wi] : nameWords[wi];
            if (ctx.measureText(tryLine).width > maxNameW && testLine) {
                line1 = testLine;
                line2 = nameWords.slice(wi).join(' ');
                break;
            }
            testLine = tryLine;
        }
        if (!line1) line1 = f.name || '';

        var nameStartY = h * 0.14 + nameSz;
        txt(ctx, line1, tx, nameStartY, nameFontStr(preset, nameSz), '#1C1814');
        var nameEndY;
        if (line2) {
            txt(ctx, line2, tx, nameStartY + nameSz * 1.15, nameFontStr(preset, nameSz), '#1C1814');
            nameEndY = nameStartY + nameSz * 2.2;
        } else {
            nameEndY = nameStartY + nameSz * 0.6;
        }

        var origY = nameEndY + subSz * 1.8;
        txt(ctx, (f.origin || '').toUpperCase(), tx, origY, bodyFontStr(preset, subSz, 600), '#999590');

        var sepY = origY + subSz * 2.6;
        ctx.strokeStyle = '#E8E4E0'; ctx.lineWidth = 0.75;
        ctx.beginPath(); ctx.moveTo(tx, sepY); ctx.lineTo(textW - 18, sepY); ctx.stroke();

        txt(ctx, f.process,     tx, sepY + bodySz * 2.6, bodyFontStr(preset, bodySz, 500), '#777370');
        txt(ctx, f.roastLevel,  tx, h * 0.72,             bodyFontStr(preset, bodySz, 600), '#4A4540');
        txt(ctx, f.flavorNotes, tx, h * 0.72 + bodySz * 2, bodyFontStr(preset, bodySz),    '#888480');
        txt(ctx, f.roastDate ? ('Roasted on: ' + f.roastDate) : '', tx, h - 18,
            bodyFontStr(preset, bodySz * 0.88, 500), '#BBB7B3');
    }

    // ════════════════════════════════════════════════════
    // T2 — Ink (dark, full-bleed bg or rich gradient)
    // ════════════════════════════════════════════════════
    function renderInk(ctx, w, h, f, accent, img, preset) {
        // Background — image or dark gradient
        if (img) {
            ctx.save();
            ctx.beginPath(); ctx.rect(0, 0, w, h); ctx.clip();
            drawImageContain(ctx, img, 0, 0, w, h);
            // Dark overlay
            var ov = ctx.createLinearGradient(0, 0, w, h);
            ov.addColorStop(0, 'rgba(18,12,8,0.82)');
            ov.addColorStop(1, 'rgba(18,12,8,0.72)');
            ctx.fillStyle = ov; ctx.fillRect(0, 0, w, h);
            ctx.restore();
        } else {
            var bg = ctx.createLinearGradient(0, 0, w, h);
            bg.addColorStop(0, '#1A1210'); bg.addColorStop(0.6, '#141008'); bg.addColorStop(1, '#1E160E');
            ctx.fillStyle = bg; ctx.fillRect(0, 0, w, h);
            // Warm glow
            var glow = ctx.createRadialGradient(0, 0, 0, 0, 0, Math.max(w, h) * 0.7);
            glow.addColorStop(0, 'rgba(155,106,106,0.18)'); glow.addColorStop(1, 'transparent');
            ctx.fillStyle = glow; ctx.fillRect(0, 0, w, h);
            // Grain
            ctx.save(); ctx.globalAlpha = 0.025;
            for (var i = 0; i < 400; i++) {
                ctx.fillStyle = '#C9A87A';
                ctx.fillRect(Math.random() * w, Math.random() * h, 1.5, 1.5);
            }
            ctx.globalAlpha = 1; ctx.restore();
        }

        // Top accent line
        ctx.fillStyle = accent;
        ctx.fillRect(0, 0, w, Math.max(2.5, h * 0.007));

        // Bottom fade
        var fade = ctx.createLinearGradient(0, h - h * 0.18, 0, h);
        fade.addColorStop(0, 'transparent'); fade.addColorStop(1, 'rgba(0,0,0,0.4)');
        ctx.fillStyle = fade; ctx.fillRect(0, h - h * 0.18, w, h * 0.18);

        var mx     = w * 0.07;
        var nameSz = Math.max(24, Math.min(54, w * 0.12));
        var subSz  = Math.max(9,  Math.min(14, w * 0.030));
        var bodySz = Math.max(8,  Math.min(12, w * 0.025));

        txt(ctx, f.name, mx, h * 0.18 + nameSz * 0.5, nameFontStr(preset, nameSz), '#F0ECE5');

        var origY = h * 0.18 + nameSz + subSz * 1.5;
        txt(ctx, (f.origin||'').toUpperCase(), mx, origY, bodyFontStr(preset, subSz, 600), accent);

        var ruleY = origY + subSz * 2.4;
        ctx.strokeStyle = '#2E2420'; ctx.lineWidth = 0.75;
        ctx.beginPath(); ctx.moveTo(mx, ruleY); ctx.lineTo(w - mx, ruleY); ctx.stroke();

        txt(ctx, f.process,    mx, ruleY + bodySz * 2.6,  bodyFontStr(preset, bodySz),      '#7A7470');
        txt(ctx, f.roastLevel, mx, ruleY + bodySz * 6.2,  bodyFontStr(preset, bodySz, 600), '#C8C4BE');
        txt(ctx, f.flavorNotes,mx, ruleY + bodySz * 8.4,  bodyFontStr(preset, bodySz),      '#6A6560');

        // Origin ghost stamp bottom-right
        ctx.save(); ctx.globalAlpha = 0.10;
        txt(ctx, (f.origin||'').toUpperCase(), w - mx, h - 18, nameFontStr(preset, Math.max(14, w * 0.04)), '#C9A87A', 'right');
        ctx.globalAlpha = 1; ctx.restore();

        txt(ctx, f.roastDate ? ('Roasted: ' + f.roastDate) : '', mx, h - 18, bodyFontStr(preset, bodySz * 0.9, 500), '#4A4540');
    }

    // ════════════════════════════════════════════════════
    // T4 — Strip (minimal Swiss, left accent band)
    // ════════════════════════════════════════════════════
    function renderStrip(ctx, w, h, f, accent, img, preset) {
        ctx.fillStyle = '#FDFCFB'; ctx.fillRect(0, 0, w, h);

        var bandW = Math.round(w * 0.065);
        ctx.fillStyle = accent; ctx.fillRect(0, 0, bandW, h);

        // Rotated origin in band
        ctx.save();
        ctx.translate(bandW / 2, h / 2); ctx.rotate(-Math.PI / 2);
        ctx.fillStyle = 'rgba(255,255,255,0.82)';
        ctx.font = '700 ' + Math.max(8, bandW * 0.28) + "px 'Inter', sans-serif";
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText((f.origin || '').toUpperCase(), 0, 0);
        ctx.restore();

        var cx2    = bandW + w * 0.05;
        var cw     = w - cx2 - w * 0.04;
        var pillH  = Math.max(14, h * 0.065);
        var pillSz = Math.max(7, pillH * 0.48);

        roundRect(ctx, cx2, h * 0.07, cw * 0.38, pillH, 3, '#F0EDE8');
        txt(ctx, (f.process||'').toUpperCase(), cx2 + 9, h * 0.07 + pillH / 2,
            '600 ' + pillSz + "px 'Inter', sans-serif", '#999590', 'left', 'middle');

        var nameSz = Math.max(20, Math.min(52, w * 0.112));
        txt(ctx, f.name, cx2, h * 0.07 + pillH + nameSz * 1.12, nameFontStr(preset, nameSz), '#1A1714');

        var ruleY2 = h * 0.07 + pillH + nameSz * 1.56 + 6;
        ctx.strokeStyle = '#E0DDD8'; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(cx2, ruleY2); ctx.lineTo(w - w * 0.04, ruleY2); ctx.stroke();

        var bodySz = Math.max(8, Math.min(12, w * 0.026));
        var col2   = cx2 + cw * 0.5;
        var infoY  = ruleY2 + bodySz * 2.2;

        txt(ctx, 'ROAST', cx2,  infoY, bodyFontStr(preset, bodySz * 0.78, 600), '#B0ACA8');
        txt(ctx, 'NOTES', col2, infoY, bodyFontStr(preset, bodySz * 0.78, 600), '#B0ACA8');
        txt(ctx, f.roastLevel, cx2, infoY + bodySz * 2.1, bodyFontStr(preset, bodySz, 600), '#3A3530');

        var notes = (f.flavorNotes || '').split(', ');
        txt(ctx, notes.slice(0, 2).join(', '), col2, infoY + bodySz * 2.1, bodyFontStr(preset, bodySz), '#706C68');
        if (notes[2]) txt(ctx, notes[2], col2, infoY + bodySz * 3.7, bodyFontStr(preset, bodySz), '#706C68');

        var botY2 = h - h * 0.14;
        ctx.strokeStyle = '#E8E5E0'; ctx.lineWidth = 0.75;
        ctx.beginPath(); ctx.moveTo(cx2, botY2); ctx.lineTo(w - w * 0.04, botY2); ctx.stroke();
        txt(ctx, f.roastDate ? ('Roasted on: ' + f.roastDate) : '', cx2, h - h * 0.06,
            bodyFontStr(preset, bodySz * 0.85, 500), '#B0ACA8', 'left', 'middle');
    }

    // ════════════════════════════════════════════════════
    // T5 — Washi (craft paper, centred, ornamental)
    // ════════════════════════════════════════════════════
    function renderWashi(ctx, w, h, f, accent, img, preset) {
        // Background — image or kraft gradient
        if (img) {
            ctx.save();
            ctx.beginPath(); ctx.rect(0, 0, w, h); ctx.clip();
            drawImageContain(ctx, img, 0, 0, w, h);
            var washiOv = ctx.createLinearGradient(0, 0, 0, h);
            washiOv.addColorStop(0, 'rgba(246,237,216,0.82)');
            washiOv.addColorStop(1, 'rgba(234,224,194,0.85)');
            ctx.fillStyle = washiOv; ctx.fillRect(0, 0, w, h);
            ctx.restore();
        } else {
            var kbg = ctx.createLinearGradient(0, 0, w, h);
            kbg.addColorStop(0, '#F6EDD8'); kbg.addColorStop(0.5, '#F0E6C8'); kbg.addColorStop(1, '#EBE0C2');
            ctx.fillStyle = kbg; ctx.fillRect(0, 0, w, h);
            ctx.save(); ctx.globalAlpha = 0.04;
            for (var gi = 0; gi < 350; gi++) {
                ctx.fillStyle = '#5A4020';
                ctx.fillRect(Math.random() * w, Math.random() * h, 1.5, 1.5);
            }
            ctx.globalAlpha = 1; ctx.restore();
        }

        // Double border
        var bm = 10;
        ctx.strokeStyle = '#C8B898'; ctx.lineWidth = 1.5;
        ctx.strokeRect(bm, bm, w - bm * 2, h - bm * 2);
        ctx.strokeStyle = '#DDD0B0'; ctx.lineWidth = 0.5;
        ctx.strokeRect(bm + 5, bm + 5, w - bm * 2 - 10, h - bm * 2 - 10);

        // Corner dots
        [[bm + 5, bm + 5],[w - bm - 5, bm + 5],[bm + 5, h - bm - 5],[w - bm - 5, h - bm - 5]].forEach(function(c) {
            ctx.fillStyle = accent;
            ctx.beginPath(); ctx.arc(c[0], c[1], 2.5, 0, Math.PI * 2); ctx.fill();
        });

        // Origin top rule
        var topY2 = h * 0.12;
        ctx.strokeStyle = '#C0AA80'; ctx.lineWidth = 0.75;
        ctx.beginPath(); ctx.moveTo(bm + 18, topY2); ctx.lineTo(w / 2 - 44, topY2); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(w / 2 + 44, topY2); ctx.lineTo(w - bm - 18, topY2); ctx.stroke();
        txt(ctx, (f.origin||'').toUpperCase(), w / 2, topY2,
            bodyFontStr(preset, Math.max(9, w * 0.022), 600), '#9A8060', 'center', 'middle');

        // Name
        var nameSz = Math.max(20, Math.min(52, w * 0.112));
        txt(ctx, f.name, w / 2, h * 0.38, nameFontStr(preset, nameSz), '#2A2018', 'center', 'middle');

        // Diamond ornament
        var midY2 = h * 0.38 + nameSz * 0.7;
        ctx.strokeStyle = accent; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(bm + 18, midY2); ctx.lineTo(w / 2 - 9, midY2); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(w / 2 + 9, midY2); ctx.lineTo(w - bm - 18, midY2); ctx.stroke();
        ctx.fillStyle = accent;
        ctx.beginPath();
        ctx.moveTo(w / 2, midY2 - 5); ctx.lineTo(w / 2 + 5, midY2);
        ctx.lineTo(w / 2, midY2 + 5); ctx.lineTo(w / 2 - 5, midY2);
        ctx.closePath(); ctx.fill();

        var bodySz = Math.max(8, Math.min(12, w * 0.026));
        txt(ctx, (f.process||'').toUpperCase(), w / 2, midY2 + bodySz * 2.6,
            bodyFontStr(preset, bodySz, 500), '#8A7860', 'center', 'middle');
        txt(ctx, f.roastLevel, w / 2, h * 0.67, bodyFontStr(preset, bodySz, 600), '#5A4830', 'center', 'middle');
        txt(ctx, f.flavorNotes, w / 2, h * 0.67 + bodySz * 2.2, bodyFontStr(preset, bodySz), '#8A7860', 'center', 'middle');

        // Bottom
        var by2 = h - h * 0.14;
        ctx.strokeStyle = '#C0AA80'; ctx.lineWidth = 0.75;
        ctx.beginPath(); ctx.moveTo(bm + 18, by2); ctx.lineTo(w - bm - 18, by2); ctx.stroke();
        txt(ctx, f.roastDate ? ('Roasted on: ' + f.roastDate) : '', bm + 20, h - h * 0.065,
            bodyFontStr(preset, bodySz * 0.9, 500), '#9A8060', 'left', 'middle');
    }

    // ── Public API ───────────────────────────────────────────────────
    return {
        RENDER_SCALE:  RENDER_SCALE,
        FONT_PRESETS:  FONT_PRESETS,
        ASPECT_RATIOS: ASPECT_RATIOS,
        templates:     TEMPLATES,
        getTemplate:   getTemplate,
        renderLabel:   renderLabel,
        loadImage:     loadImage,
    };

})();
