var startPos = {x: 0, y: 0};

interact('.draggable')
    .draggable({
        onmove: dragMoveListener,
        onstart: dragStartListener,
        inertia: true,
        // snap: {
        //     targets: [startPos],
        //     range: Infinity,
        //     relativePoints: [{x: 0.5, y: 0.5}],
        //     endOnly: true
        // }
    }).on('dragstart', function (event) {
        // Otherwise, while dragging the whole page would be selected
        document.body.classList.add("prevent-select");
        // snap to the start position
        // event.interactable.snap({ anchors: [startPos] });
    }).on('dragend', function (event) {
        // Otherwise, while dragging the whole page would be selected
        document.body.classList.remove("prevent-select");
    });

interact('.dropzone')
    .dropzone({
        accept: '.draggable',
        overlap: 0.5,
        ondrop: function (event) {
            event.stopImmediatePropagation();
            var draggableElement = event.relatedTarget;
            // Remove used elements
            draggableElement.remove();
            // Trigger HTMX POST
            // todo ich brauch hier die ID, will er aber nicht, das event wird dann nicht erkannt
            const newEvent = new Event('interactjs:dropWarrior');
            document.body.dispatchEvent(newEvent);
        },
        ondragenter: function (event) {
            var draggableElement = event.relatedTarget,
                dropzoneElement = event.target;
            dropzoneElement.classList.add('uk-card-secondary');
            draggableElement.classList.add('uk-card-secondary');
        },
        ondragleave: function (event) {
            var draggableElement = event.relatedTarget,
                dropzoneElement = event.target;
            dropzoneElement.classList.remove('uk-card-secondary');
            draggableElement.classList.remove('uk-card-secondary');
        },
        checker: function (
            dragEvent,         // related dragmove or dragend
            event,             // Touch, Pointer or Mouse Event
            dropped,           // bool default checker result
            dropzone,          // dropzone Interactable
            dropzoneElement,   // dropzone element
            draggable,         // draggable Interactable
            draggableElement   // draggable element
        ) {
            var draggableFaction = draggableElement.getAttribute('data-faction');
            var dropzoneFaction = dropzoneElement.getAttribute('data-faction');
            return dropped && draggableFaction !== dropzoneFaction;
        }
    });


function dragMoveListener(event) {
    var target = event.target,
        // keep the dragged position in the data-x/data-y attributes
        x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx,
        y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;

    // translate the element
    target.style.webkitTransform =
        target.style.transform =
            'translate(' + x + 'px, ' + y + 'px)';

    // update the position attributes
    target.setAttribute('data-x', x);
    target.setAttribute('data-y', y);
}

function dragStartListener(event) {
    var rect = interact.getElementRect(event.target);

    // record center point when starting a drag
    startPos.x = rect.left + rect.width / 2;
    startPos.y = rect.top + rect.height / 2;
}