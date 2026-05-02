var StickerSheetCreator = (function () {
    var MAX_IMAGES = 4;
    var MAX_FILE_SIZE = 10 * 1024 * 1024;
    var PRINT_DPI = 300;

    var TEMPLATE = {
        id: 'us4',
        name: 'US-4',
        sheetWidthIn: 8.5,
        sheetHeightIn: 11,
        slotWidthIn: 4,
        slotHeightIn: 5,
        slots: [
            { label: 'Top-left', x: 0.17, y: 0.5 },
            { label: 'Top-right', x: 4.33, y: 0.5 },
            { label: 'Bottom-left', x: 0.17, y: 5.5 },
            { label: 'Bottom-right', x: 4.33, y: 5.5 },
        ],
    };

    var initialized = false;
    var state = getInitialState();
    var els = {};

    function getInitialState() {
        return {
            images: [],
            slots: TEMPLATE.slots.map(function () {
                return { imageId: null };
            }),
            message: '',
        };
    }

    function init() {
        if (initialized) return;
        els.modal = document.getElementById('stickerSheetModal');
        els.fileInput = document.getElementById('stickerImageInput');
        els.imageList = document.getElementById('stickerImageList');
        els.preview = document.getElementById('stickerSheetPreview');
        els.validation = document.getElementById('stickerValidation');
        els.fileStatus = document.getElementById('stickerFileStatus');
        els.downloadButton = document.getElementById('stickerDownloadButton');

        if (!els.modal || !els.fileInput || !els.imageList || !els.preview) return;

        els.fileInput.addEventListener('change', function (event) {
            handleFiles(event.target.files || []);
            event.target.value = '';
        });

        window.addEventListener('resize', updatePreviewFits);
        initialized = true;
    }

    function open() {
        init();
        if (!initialized) return;
        els.modal.style.display = 'block';
        render();
    }

    function close() {
        init();
        if (els.modal) els.modal.style.display = 'none';
    }

    function readFileAsDataURL(file) {
        return new Promise(function (resolve, reject) {
            var reader = new FileReader();
            reader.onload = function () { resolve(reader.result); };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    function loadImage(dataUrl) {
        return new Promise(function (resolve, reject) {
            var img = new Image();
            img.onload = function () { resolve(img); };
            img.onerror = reject;
            img.src = dataUrl;
        });
    }

    function rotateImageClockwise(img) {
        var canvas = document.createElement('canvas');
        canvas.width = img.naturalHeight;
        canvas.height = img.naturalWidth;
        var ctx = canvas.getContext('2d');
        ctx.translate(canvas.width, 0);
        ctx.rotate(Math.PI / 2);
        ctx.drawImage(img, 0, 0);
        return canvas.toDataURL('image/png');
    }

    async function prepareImage(file, quantity) {
        var originalDataUrl = await readFileAsDataURL(file);
        var originalImg = await loadImage(originalDataUrl);
        var displayDataUrl = originalDataUrl;
        var wasRotated = false;

        if (originalImg.naturalWidth > originalImg.naturalHeight) {
            displayDataUrl = rotateImageClockwise(originalImg);
            wasRotated = true;
        }

        var displayImg = wasRotated ? await loadImage(displayDataUrl) : originalImg;
        return {
            id: 'sticker-image-' + Date.now() + '-' + Math.random().toString(36).slice(2),
            name: file.name,
            size: file.size,
            quantity: quantity,
            dataUrl: displayDataUrl,
            element: displayImg,
            width: displayImg.naturalWidth,
            height: displayImg.naturalHeight,
            wasRotated: wasRotated,
        };
    }

    async function handleFiles(fileList) {
        var files = Array.prototype.slice.call(fileList);
        var accepted = [];
        var messages = [];

        files.forEach(function (file) {
            if (state.images.length + accepted.length >= MAX_IMAGES) {
                messages.push('Maximum 4 images per sheet.');
            } else if (!file.type || file.type.indexOf('image/') !== 0) {
                messages.push(file.name + ' is not an image.');
            } else if (file.size > MAX_FILE_SIZE) {
                messages.push(file.name + ' is larger than 10 MB.');
            } else {
                accepted.push(file);
            }
        });

        if (!accepted.length) {
            state.message = messages[0] || 'No images selected.';
            render();
            return;
        }

        state.message = 'Reading images...';
        render();

        for (var i = 0; i < accepted.length; i++) {
            var quantity = defaultQuantityForNewImage(accepted.length);
            try {
                state.images.push(await prepareImage(accepted[i], quantity));
            } catch (e) {
                messages.push('Could not read ' + accepted[i].name + '.');
            }
        }

        state.message = messages[0] || '';
        rebuildSlots();
        render();
    }

    function defaultQuantityForNewImage(batchSize) {
        if (!state.images.length && batchSize === 1) return 4;
        var remaining = 4 - totalQuantity();
        return remaining > 0 ? 1 : 1;
    }

    function totalQuantity() {
        return state.images.reduce(function (sum, image) {
            return sum + (Number(image.quantity) || 0);
        }, 0);
    }

    function getImage(imageId) {
        return state.images.find(function (image) { return image.id === imageId; }) || null;
    }

    function clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    }

    function rebuildSlots() {
        var expanded = [];
        state.images.forEach(function (image) {
            var quantity = clamp(parseInt(image.quantity, 10) || 1, 1, 4);
            image.quantity = quantity;
            for (var i = 0; i < quantity; i++) expanded.push(image.id);
        });

        state.slots = TEMPLATE.slots.map(function (_slot, index) {
            var imageId = expanded[index] || null;
            return { imageId: imageId };
        });
    }

    function render() {
        if (!initialized) return;
        renderImageList();
        renderPreview();
        renderValidation();
        setTimeout(updatePreviewFits, 0);
    }

    function renderImageList() {
        els.imageList.innerHTML = '';

        if (!state.images.length) {
            var empty = document.createElement('div');
            empty.className = 'sticker-empty-state';
            empty.textContent = 'No images selected.';
            els.imageList.appendChild(empty);
            return;
        }

        state.images.forEach(function (image) {
            var item = document.createElement('div');
            item.className = 'sticker-image-item';
            item.dataset.imageId = image.id;

            var thumb = document.createElement('img');
            thumb.src = image.dataUrl;
            thumb.alt = image.name;
            thumb.className = 'sticker-image-thumb';

            var meta = document.createElement('div');
            meta.className = 'sticker-image-meta';

            var name = document.createElement('div');
            name.className = 'sticker-image-name';
            name.textContent = image.name;

            var sub = document.createElement('div');
            sub.className = 'sticker-image-sub';
            sub.textContent = image.wasRotated ? 'Auto-rotated to portrait' : 'Portrait fit';

            meta.appendChild(name);
            meta.appendChild(sub);

            var qtyWrap = document.createElement('label');
            qtyWrap.className = 'sticker-qty-control';
            qtyWrap.textContent = 'Qty';

            var qty = document.createElement('input');
            qty.type = 'number';
            qty.min = '1';
            qty.max = '4';
            qty.step = '1';
            qty.value = image.quantity;
            qty.setAttribute('aria-label', 'Sticker quantity for ' + image.name);
            qty.addEventListener('input', function () {
                image.quantity = clamp(parseInt(qty.value, 10) || 1, 1, 4);
                qty.value = image.quantity;
                rebuildSlots();
                render();
            });
            qtyWrap.appendChild(qty);

            var remove = document.createElement('button');
            remove.type = 'button';
            remove.className = 'btn-icon sticker-remove-btn';
            remove.title = 'Remove image';
            remove.setAttribute('aria-label', 'Remove ' + image.name);
            remove.innerHTML = '<span class="material-icons">close</span>';
            remove.addEventListener('click', function () {
                state.images = state.images.filter(function (candidate) {
                    return candidate.id !== image.id;
                });
                rebuildSlots();
                render();
            });

            item.appendChild(thumb);
            item.appendChild(meta);
            item.appendChild(qtyWrap);
            item.appendChild(remove);
            els.imageList.appendChild(item);
        });
    }

    function renderPreview() {
        els.preview.innerHTML = '';
        els.preview.style.setProperty('--sheet-width', TEMPLATE.sheetWidthIn);
        els.preview.style.setProperty('--sheet-height', TEMPLATE.sheetHeightIn);

        TEMPLATE.slots.forEach(function (slotSpec, index) {
            var slotState = state.slots[index] || {};
            var slotEl = document.createElement('div');
            slotEl.className = 'sticker-slot';
            slotEl.dataset.slotIndex = index;
            slotEl.style.left = (slotSpec.x / TEMPLATE.sheetWidthIn * 100) + '%';
            slotEl.style.top = (slotSpec.y / TEMPLATE.sheetHeightIn * 100) + '%';
            slotEl.style.width = (TEMPLATE.slotWidthIn / TEMPLATE.sheetWidthIn * 100) + '%';
            slotEl.style.height = (TEMPLATE.slotHeightIn / TEMPLATE.sheetHeightIn * 100) + '%';
            slotEl.setAttribute('role', 'img');
            slotEl.setAttribute('aria-label', slotSpec.label + ' sticker slot');

            var number = document.createElement('span');
            number.className = 'sticker-slot-number';
            number.textContent = String(index + 1);
            slotEl.appendChild(number);

            var image = slotState.imageId ? getImage(slotState.imageId) : null;
            if (image) {
                var img = document.createElement('img');
                img.src = image.dataUrl;
                img.alt = '';
                img.draggable = false;
                img.className = 'sticker-slot-image';
                slotEl.appendChild(img);
            } else {
                var placeholder = document.createElement('span');
                placeholder.className = 'sticker-slot-placeholder';
                placeholder.textContent = 'Empty';
                slotEl.appendChild(placeholder);
            }

            els.preview.appendChild(slotEl);
        });
    }

    function renderValidation() {
        var total = totalQuantity();
        var jsPDF = window.jspdf && window.jspdf.jsPDF;
        var message = state.message;
        var ready = state.images.length > 0 && total > 0 && jsPDF;
        var warning = false;

        if (!state.images.length) {
            message = message || 'Select 1 to 4 images to fill the sheet.';
        } else if (!jsPDF) {
            message = 'PDF export is unavailable because jsPDF did not load.';
        } else if (total !== 4) {
            warning = true;
            if (total < 4) {
                message = 'Warning: only ' + total + ' sticker slot' + (total === 1 ? '' : 's') + ' selected; remaining slots export blank.';
            } else {
                message = 'Warning: ' + total + ' sticker slots selected; only the first 4 export.';
            }
        } else {
            message = 'Ready: 4 sticker slots selected.';
        }

        els.validation.textContent = message;
        els.validation.classList.toggle('is-ready', ready);
        els.validation.classList.toggle('is-warning', warning);
        els.downloadButton.disabled = !ready;
        if (els.fileStatus) els.fileStatus.textContent = state.images.length + ' / 4 images';
    }

    function getSlotMetrics(index) {
        var slot = state.slots[index];
        var image = slot && slot.imageId ? getImage(slot.imageId) : null;
        var slotEl = els.preview.querySelector('[data-slot-index="' + index + '"]');
        if (!image || !slotEl) return null;

        var rect = slotEl.getBoundingClientRect();
        if (!rect.width || !rect.height) return null;

        var scale = Math.max(rect.width / image.width, rect.height / image.height);
        var fitWidth = image.width * scale;
        var fitHeight = image.height * scale;
        return {
            slotEl: slotEl,
            image: image,
            width: rect.width,
            height: rect.height,
            fitWidth: fitWidth,
            fitHeight: fitHeight,
        };
    }

    function updatePreviewFits() {
        if (!initialized || !els.preview) return;
        state.slots.forEach(function (slot, index) {
            var metrics = getSlotMetrics(index);
            if (!metrics) return;
            var img = metrics.slotEl.querySelector('.sticker-slot-image');
            if (!img) return;
            img.style.width = metrics.fitWidth + 'px';
            img.style.height = metrics.fitHeight + 'px';
            img.style.transform = 'translate(-50%, -50%)';
        });
    }

    function renderSlotCanvas(image) {
        var outWidth = TEMPLATE.slotWidthIn * PRINT_DPI;
        var outHeight = TEMPLATE.slotHeightIn * PRINT_DPI;
        var canvas = document.createElement('canvas');
        canvas.width = outWidth;
        canvas.height = outHeight;
        var ctx = canvas.getContext('2d');
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, outWidth, outHeight);

        var scale = Math.max(outWidth / image.width, outHeight / image.height);
        var cropWidth = outWidth / scale;
        var cropHeight = outHeight / scale;
        var sx = Math.max(0, (image.width - cropWidth) / 2);
        var sy = Math.max(0, (image.height - cropHeight) / 2);

        ctx.drawImage(image.element, sx, sy, cropWidth, cropHeight, 0, 0, outWidth, outHeight);
        return canvas;
    }

    function downloadPDF() {
        init();
        if (!state.images.length || totalQuantity() < 1) {
            renderValidation();
            return;
        }

        var jsPDF = window.jspdf && window.jspdf.jsPDF;
        if (!jsPDF) {
            renderValidation();
            return;
        }

        var pdf = new jsPDF({
            orientation: 'portrait',
            unit: 'in',
            format: 'letter',
            compress: true,
        });

        TEMPLATE.slots.forEach(function (slotSpec, index) {
            var slot = state.slots[index];
            var image = slot && slot.imageId ? getImage(slot.imageId) : null;
            if (!image) return;
            var canvas = renderSlotCanvas(image);
            var dataUrl = canvas.toDataURL('image/jpeg', 0.92);
            pdf.addImage(
                dataUrl,
                'JPEG',
                slotSpec.x,
                slotSpec.y,
                TEMPLATE.slotWidthIn,
                TEMPLATE.slotHeightIn,
                undefined,
                'FAST'
            );
        });

        pdf.save('us4_stickers.pdf');
    }

    return {
        open: open,
        close: close,
        downloadPDF: downloadPDF,
        template: TEMPLATE,
    };
})();
