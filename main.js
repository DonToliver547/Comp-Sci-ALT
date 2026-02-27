// =====================
// BUTTONS
// =====================
input.onButtonPressed(Button.A, function () {
    basic.clearScreen()
    light2 = input.lightLevel()
    if (light2 < 30) {
        // Night / very dark — moon shape
        basic.showLeds(`
            . # # . .
            # . . # .
            # . . # .
            # . . # .
            . # # . .
            `)
        basic.pause(2000)
    } else if (light2 < 85) {
        // Dusk / dim — half sun
        basic.showLeds(`
            . . # . .
            . # # . .
            # # # . .
            . # # . .
            . . # . .
            `)
        basic.pause(2000)
    } else if (light2 < 170) {
        // Normal daylight — sun outline
        basic.showLeds(`
            . . # . .
            . # . # .
            # . . . #
            . # . # .
            . . # . .
            `)
        basic.pause(2000)
    } else {
        // High sunlight (≥170) — full blazing sun, adds +1 to fire risk
        basic.showLeds(`
            # . # . #
            . # # # .
            # # # # #
            . # # # .
            # . # . #
            `)
        basic.pause(2000)
    }
})
// Button B: show current temperature
input.onButtonPressed(Button.B, function () {
    basic.clearScreen()
    basic.showNumber(currenttemp)
})
let light22 = 0
let currenttemp = 0
let light2 = 0
let previoustemp = input.temperature()
datalogger.deleteLog(datalogger.DeleteType.Full)
basic.forever(function () {
    currenttemp = input.temperature()
    light22 = input.lightLevel()
    // ── DISPLAY based on temperature ──
    // These must be separate if-blocks, NOT else-if,
    // so that frost and drop checks are never skipped.
    if (currenttemp > 35) {
        // Critical heat — exclamation + alarm
        basic.showLeds(`
            . . # . .
            . . # . .
            . . # . .
            . . . . .
            . . # . .
            `)
        music.play(music.stringPlayable("C C C C C C C C ", 120), music.PlaybackMode.UntilDone)
    } else if (currenttemp < 0) {
        // Freezing — X icon
        // Must come BEFORE the general "below 35" check
        basic.showLeds(`
            # . . . #
            . # . # .
            . . # . .
            . # . # .
            # . . . #
            `)
    } else {
        // Normal — tick
        basic.showLeds(`
            . . . . #
            . . . # .
            # . # . .
            . # . . .
            . . . . .
            `)
    }
    // ── SUDDEN CHANGE DETECTION ──
    // Separate if-blocks so both can trigger independently
    if (currenttemp > previoustemp + 3) {
        // Sudden spike — up arrow
        basic.showLeds(`
            . . # . .
            . # # # .
            # . # . #
            . . # . .
            . . # . .
            `)
        basic.pause(1000)
    }
    if (currenttemp < previoustemp - 3) {
        // Sudden drop — down arrow
        basic.showLeds(`
            . . # . .
            . . # . .
            # . # . #
            . # # # .
            . . # . .
            `)
        basic.pause(1000)
    }
    previoustemp = currenttemp
    basic.pause(1000)
})
// =====================
// ADAPTIVE LOGGING LOOP
// =====================
basic.forever(function () {
    datalogger.log(
    datalogger.createCV("light value", input.lightLevel()),
    datalogger.createCV("temperature value", currenttemp)
    )
    basic.pause(3000)
})
