const position = {x: 0, y: 0}

interact('.draggable')
    .draggable({
        listeners: {
            start(event) {
                console.log(event.type, event.target)
            },
            move(event) {
                position.x += event.dx
                position.y += event.dy

                event.target.style.transform =
                    `translate(${position.x}px, ${position.y}px)`
            },
        },
        modifiers: [
            interact.modifiers.snap({
                targets: [{x: 300, y: 300}],
                relativePoints: [
                    {x: 0, y: 0},   // snap relative to the element's top-left,
                    {x: 0.5, y: 0.5},   // to the center
                    {x: 1, y: 1}    // and to the bottom-right
                ]
            })
        ]
    })

interact('.dropzone')
    .dropzone({
        ondrop: function (event) {
            alert(event.relatedTarget.id
                + ' was dropped into '
                + event.target.id)
        }
    })
    .on('dropactivate', function (event) {
        event.target.classList.add('drop-activated')
    })
