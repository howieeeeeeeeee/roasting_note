var LabelCreator = (function () {
    var RENDER_SCALE = 5;

    var templates = {
        minimal: {
            id: 'minimal',
            name: 'Minimal',
            width: 500,
            height: 400,
            exportWidthCm: 5,
            exportHeightCm: 4,
            backgroundColor: '#FFFFFF',
            accentBar: true,
            accentBarX: 14,
            accentBarY: 28,
            accentBarWidth: 5,
            accentBarHeight: 0.6,
            uppercase: true,
            // Image frame: right half, 80% area, centered
            imageFrame: {
                // The frame region (right half)
                xPct: 0.55, yPct: 0.0, widthPct: 0.45, heightPct: 1.0,
                // Image fills 80% of frame, centered
                imagePct: 0.80
            },
            decorations: [
                { type: 'line', x1Pct: 0.545, y1Pct: 0.02, x2Pct: 0.545, y2Pct: 0.98, color: '#E0E0E0', width: 1 }
            ],
            fields: [
                { key: 'name', xPct: 0.048, yPct: 0.115, fontSize: 28, fontFamily: 'Inter', fontWeight: 'bold', align: 'left', color: '#2C2C2C' },
                { key: 'origin', xPct: 0.048, yPct: 0.195, fontSize: 17, fontFamily: 'Inter', fontWeight: 'normal', align: 'left', color: '#777777' },
                { key: 'process', xPct: 0.048, yPct: 0.325, fontSize: 13, fontFamily: 'Inter', fontWeight: 'bold', align: 'left', color: '#555555' },
                { key: 'roastLevel', xPct: 0.048, yPct: 0.535, fontSize: 13, fontFamily: 'Inter', fontWeight: 'bold', align: 'left', color: '#555555' },
                { key: 'flavorNotes', xPct: 0.048, yPct: 0.600, fontSize: 12, fontFamily: 'Inter', fontWeight: 'normal', align: 'left', color: '#666666' },
                { key: 'roastDate', xPct: 0.048, yPct: 0.925, fontSize: 10, fontFamily: 'Inter', fontWeight: 'bold', align: 'left', color: '#555555', prefix: 'Roasted on: ' }
            ]
        },
        classic: {
            id: 'classic',
            name: 'Classic',
            width: 400,
            height: 250,
            exportWidthCm: 5,
            exportHeightCm: 4,
            backgroundColor: '#FFFFFF',
            accentBar: true,
            accentBarX: 10,
            accentBarY: 15,
            accentBarWidth: 6,
            accentBarHeight: 0.65,
            imageFrame: {
                xPct: 0.55, yPct: 0.0, widthPct: 0.45, heightPct: 0.72,
                imagePct: 0.80
            },
            fields: [
                { key: 'name', xPct: 0.075, yPct: 0.16, fontSize: 22, fontFamily: '"Roboto Slab", serif', fontWeight: 'bold', align: 'left', color: '#2C2C2C' },
                { key: 'origin', xPct: 0.075, yPct: 0.30, fontSize: 13, fontFamily: '"Roboto Slab", serif', fontWeight: 'normal', align: 'left', color: '#555555' },
                { key: 'process', xPct: 0.075, yPct: 0.40, fontSize: 12, fontFamily: '"Roboto Slab", serif', fontWeight: 'normal', align: 'left', color: '#777777' },
                { key: 'roastLevel', xPct: 0.075, yPct: 0.54, fontSize: 14, fontFamily: '"Roboto Slab", serif', fontWeight: 'bold', align: 'left', color: '#6B5B4D' },
                { key: 'flavorNotes', xPct: 0.075, yPct: 0.64, fontSize: 11, fontFamily: '"Roboto Slab", serif', fontWeight: 'normal', align: 'left', color: '#777777' },
                { key: 'roastDate', xPct: 0.075, yPct: 0.88, fontSize: 11, fontFamily: '"Roboto Slab", serif', fontWeight: 'normal', align: 'left', color: '#999999' }
            ],
            decorations: [
                { type: 'line', x1Pct: 0.065, y1Pct: 0.72, x2Pct: 0.94, y2Pct: 0.72, color: '#CCCCCC', width: 1 }
            ]
        },
        compact: {
            id: 'compact',
            name: 'Compact',
            width: 350,
            height: 200,
            exportWidthCm: 5,
            exportHeightCm: 4,
            backgroundColor: '#FAFAF8',
            fields: [
                { key: 'name', xPct: 0.50, yPct: 0.15, fontSize: 18, fontFamily: 'Inter', fontWeight: 'bold', align: 'center', color: '#333333' },
                { key: 'origin', xPct: 0.30, yPct: 0.33, fontSize: 11, fontFamily: 'Inter', fontWeight: 'normal', align: 'right', color: '#666666', label: 'Origin' },
                { key: 'process', xPct: 0.30, yPct: 0.44, fontSize: 11, fontFamily: 'Inter', fontWeight: 'normal', align: 'right', color: '#666666', label: 'Process' },
                { key: 'roastLevel', xPct: 0.30, yPct: 0.55, fontSize: 11, fontFamily: 'Inter', fontWeight: 'normal', align: 'right', color: '#666666', label: 'Roast' },
                { key: 'flavorNotes', xPct: 0.30, yPct: 0.66, fontSize: 11, fontFamily: 'Inter', fontWeight: 'normal', align: 'right', color: '#666666', label: 'Notes' },
                { key: 'roastDate', xPct: 0.30, yPct: 0.85, fontSize: 11, fontFamily: 'Inter', fontWeight: 'normal', align: 'right', color: '#666666', label: 'Date' }
            ],
            decorations: [
                { type: 'line', x1Pct: 0.06, y1Pct: 0.24, x2Pct: 0.94, y2Pct: 0.24, color: '#DDDDDD', width: 1 }
            ]
        }
    };

    // Image cache
    var imageCache = {};

    function loadImage(src) {
        if (imageCache[src]) return Promise.resolve(imageCache[src]);
        return new Promise(function (resolve) {
            var img = new Image();
            img.onload = function () {
                imageCache[src] = img;
                resolve(img);
            };
            img.onerror = function () { resolve(null); };
            img.src = src;
        });
    }

    function getTemplate(id) {
        return JSON.parse(JSON.stringify(templates[id] || templates.minimal));
    }

    function renderLabel(canvas, template, fieldValues, accentColor, imageSrc, exportSizeCm) {
        var w = template.width;
        var h = template.height;

        if (exportSizeCm) {
            var ratio = exportSizeCm.width / exportSizeCm.height;
            h = Math.round(w / ratio);
        }

        var scale = RENDER_SCALE;
        canvas.width = w * scale;
        canvas.height = h * scale;
        canvas.style.width = w + 'px';
        canvas.style.height = h + 'px';

        var ctx = canvas.getContext('2d');
        ctx.scale(scale, scale);

        // Background
        ctx.fillStyle = template.backgroundColor;
        ctx.fillRect(0, 0, w, h);

        // Border
        ctx.strokeStyle = '#E0E0E0';
        ctx.lineWidth = 0.5;
        ctx.strokeRect(0.25, 0.25, w - 0.5, h - 0.5);

        // Image frame (contain-fit, centered within 80% of frame area)
        if (template.imageFrame && imageSrc) {
            var cached = imageCache[imageSrc];
            if (cached) {
                var frame = template.imageFrame;
                var frameX = w * frame.xPct;
                var frameY = h * frame.yPct;
                var frameW = w * frame.widthPct;
                var frameH = h * frame.heightPct;
                var pct = frame.imagePct || 0.8;

                // Available area for image (80% of frame, centered)
                var areaW = frameW * pct;
                var areaH = frameH * pct;
                var areaCx = frameX + frameW / 2;
                var areaCy = frameY + frameH / 2;

                // Contain-fit: scale image to fit within area
                var imgAspect = cached.naturalWidth / cached.naturalHeight;
                var areaAspect = areaW / areaH;
                var drawW, drawH;
                if (imgAspect > areaAspect) {
                    drawW = areaW;
                    drawH = drawW / imgAspect;
                } else {
                    drawH = areaH;
                    drawW = drawH * imgAspect;
                }
                var drawX = areaCx - drawW / 2;
                var drawY = areaCy - drawH / 2;

                ctx.drawImage(cached, drawX, drawY, drawW, drawH);
            }
        }

        // Accent bar
        if (template.accentBar && accentColor) {
            var barW = template.accentBarWidth || 6;
            var barX = template.accentBarX || 12;
            var barY = template.accentBarY || 20;
            var barH = h * (template.accentBarHeight || 0.6);
            ctx.fillStyle = accentColor;
            var radius = barW / 2;
            ctx.beginPath();
            ctx.moveTo(barX + radius, barY);
            ctx.lineTo(barX + barW - radius, barY);
            ctx.arcTo(barX + barW, barY, barX + barW, barY + radius, radius);
            ctx.lineTo(barX + barW, barY + barH - radius);
            ctx.arcTo(barX + barW, barY + barH, barX + barW - radius, barY + barH, radius);
            ctx.lineTo(barX + radius, barY + barH);
            ctx.arcTo(barX, barY + barH, barX, barY + barH - radius, radius);
            ctx.lineTo(barX, barY + radius);
            ctx.arcTo(barX, barY, barX + radius, barY, radius);
            ctx.closePath();
            ctx.fill();
        }

        // Decorations
        if (template.decorations) {
            template.decorations.forEach(function (dec) {
                if (dec.type === 'line') {
                    var lx1 = dec.x1Pct !== undefined ? w * dec.x1Pct : dec.x1;
                    var ly1 = dec.y1Pct !== undefined ? h * dec.y1Pct : dec.y1;
                    var lx2 = dec.x2Pct !== undefined ? w * dec.x2Pct : dec.x2;
                    var ly2 = dec.y2Pct !== undefined ? h * dec.y2Pct : dec.y2;
                    ctx.beginPath();
                    ctx.moveTo(lx1, ly1);
                    ctx.lineTo(lx2, ly2);
                    ctx.strokeStyle = dec.color;
                    ctx.lineWidth = dec.width;
                    ctx.stroke();
                }
            });
        }

        // Fields
        template.fields.forEach(function (field) {
            var value = fieldValues[field.key] || '';
            if (!value) return;

            if (field.prefix) value = field.prefix + value;
            if (template.uppercase) value = value.toUpperCase();

            var fontSize = field.fontSize;
            var fontFamily = field.fontFamily;
            var fontWeight = field.fontWeight || 'normal';
            var color = field.color;

            var x = field.xPct !== undefined ? w * field.xPct : (field.x || 0);
            var y = field.yPct !== undefined ? h * field.yPct : (field.y || 0);
            var align = field.align || 'left';

            ctx.font = fontWeight + ' ' + fontSize + 'px ' + fontFamily + ', sans-serif';
            ctx.fillStyle = color;
            ctx.textAlign = align;
            ctx.textBaseline = 'middle';

            if (field.label) {
                ctx.font = 'bold ' + (fontSize - 1) + 'px ' + fontFamily + ', sans-serif';
                ctx.fillStyle = '#999999';
                ctx.textAlign = 'right';
                ctx.fillText(field.label + ':', x, y);
                ctx.font = fontWeight + ' ' + fontSize + 'px ' + fontFamily + ', sans-serif';
                ctx.fillStyle = color;
                ctx.textAlign = 'left';
                ctx.fillText(value, x + 10, y);
            } else {
                ctx.fillText(value, x, y);
            }
        });
    }

    return {
        RENDER_SCALE: RENDER_SCALE,
        getTemplate: getTemplate,
        renderLabel: renderLabel,
        templates: templates,
        loadImage: loadImage
    };
})();
