// =====================
// BUTTONS
// =====================
input.onButtonPressed(Button.A, function () {
    basic.clearScreen()
    light2 = input.lightLevel()
    if (light2 < 30) {
        basic.showLeds(`
            . # # . .
            # . . # .
            # . . # .
            # . . # .
            . # # . .
            `)
        basic.pause(2000)
    } else if (light2 < 85) {
        basic.showLeds(`
            . . # . .
            . # # . .
            # # # . .
            . # # . .
            . . # . .
            `)
        basic.pause(2000)
    } else if (light2 < 170) {
        basic.showLeds(`
            . . # . .
            . # . # .
            # . . . #
            . # . # .
            . . # . .
            `)
        basic.pause(2000)
    } else {
        basic.showLeds(`
            # . # . #
            . # # # .
            # # # # #
            . # # # .
            # . # . #
            `)
        basic.pause(2000)
    }
    basic.pause(2000)
})
/**
 * T is temperature
 */
/**
 * R is the risk of fire level
 */
/**
 * average temperature
 */
/**
 * waring trigger point
 */
// Button B: cycle display mode (temp → risk → baseline → threshold)
input.onButtonPressed(Button.B, function () {
    displayMode = (displayMode + 1) % 4
    basic.clearScreen()
    if (displayMode == 0) {
        basic.showString("T:")
        basic.showNumber(currenttemp)
    } else if (displayMode == 1) {
        basic.showString("R:")
        basic.showNumber(fireRisk)
    } else if (displayMode == 2) {
        basic.showString("B:")
        basic.showNumber(Math.round(rollingAvg))
    } else {
        basic.showString("TH:")
        basic.showNumber(Math.round(dynamicThreshold))
    }
    basic.clearScreen()
})
let allClearCount = 0
let alertCount = 0
let fireRisk = 0
let currenttemp = 0
let displayMode = 0
let light2 = 0
let dynamicThreshold = 0
let rollingAvg = 0
let previoustemp = input.temperature()
let logInterval = 3000
// Rolling average (virtual model)
// starts at current temp
rollingAvg = input.temperature()
// how fast the average adapts (0.1 = slow/smooth)
let avgWeight = 0.1
// Dynamic thresholds — derived from baseline, not hardcoded
// warning level: baseline + margin
dynamicThreshold = 35
// critical level: warning + extra margin
let criticalThreshold = 40
// degrees above average = warning
let warningMargin = 5
// degrees above average = critical
let criticalMargin = 10
// sustained calm loosens them back
datalogger.deleteLog(datalogger.DeleteType.Full)
basic.forever(function () {
    currenttemp = input.temperature()
    light2 = input.lightLevel()
    // --- FEEDBACK STEP 1: Update rolling average (exponential moving average) ---
    // New average = (old average * 0.9) + (new reading * 0.1)
    // This means recent temps gradually shift what "normal" looks like
    rollingAvg = rollingAvg * (1 - avgWeight) + currenttemp * avgWeight
    // --- FEEDBACK STEP 2: Recalculate dynamic thresholds from new baseline ---
    dynamicThreshold = rollingAvg + warningMargin
    criticalThreshold = rollingAvg + criticalMargin
    // --- FEEDBACK STEP 3: Score fire risk using dynamic thresholds ---
    fireRisk = 0
    // above baseline
    if (currenttemp > rollingAvg + 2) {
        fireRisk += 1
    }
    // warning zone
    if (currenttemp > dynamicThreshold) {
        fireRisk += 1
    }
    // critical zone
    if (currenttemp > criticalThreshold) {
        fireRisk += 1
    }
    // high light adds risk
    if (light2 > 170) {
        fireRisk += 1
    }
    // --- FEEDBACK STEP 4: Adapt the margins based on sustained conditions ---
    // If alerts keep firing, tighten margins (system becomes more sensitive)
    if (fireRisk >= 3) {
        alertCount += 1
        allClearCount = 0
        if (alertCount >= 4 && warningMargin > 2) {
            // become more sensitive
            warningMargin += 0 - 1
        }
    } else if (fireRisk == 0) {
        allClearCount += 1
        alertCount = 0
        if (allClearCount >= 6 && warningMargin < 7) {
            // relax back toward normal
            warningMargin += 1
        }
    }
    // criticalMargin always stays warningMargin + 5
    criticalMargin = warningMargin + 5
    // --- FEEDBACK STEP 5: Adaptive log rate ---
    if (fireRisk >= 3) {
        logInterval = 1000
    } else if (fireRisk == 2) {
        logInterval = 2000
    } else {
        logInterval = 4000
    }
    // --- DISPLAY based on risk ---
    if (fireRisk >= 3) {
        // Critical - exclamation + alarm
        basic.showLeds(`
            . . # . .
            . . # . .
            . . # . .
            . . . . .
            . . # . .
            `)
        music.play(music.stringPlayable("C C C C C C C C ", 120), music.PlaybackMode.UntilDone)
    } else if (fireRisk == 2) {
        // Warning - up arrow (rising danger)
        basic.showLeds(`
            . . # . .
            . # # # .
            # . # . #
            . . # . .
            . . # . .
            `)
    } else if (currenttemp < 0) {
        // Freezing - X
        basic.showLeds(`
            # . . . #
            . # . # .
            . . # . .
            . # . # .
            # . . . #
            `)
    } else {
        // Normal - tick
        basic.showLeds(`
            . . . . #
            . . . # .
            # . # . .
            . # . . .
            . . . . .
            `)
    }
    // --- Drastic sudden change detection (still useful on top of adaptive model) ---
    if (currenttemp > previoustemp + 3) {
        basic.showLeds(`
            . . # . .
            . # # # .
            # . # . #
            . . # . .
            . . # . .
            `)
        basic.pause(2000)
    } else if (currenttemp < previoustemp - 3) {
        basic.showLeds(`
            . . # . .
            . . # . .
            # . # . #
            . # # # .
            . . # . .
            `)
        basic.pause(2000)
    }
    previoustemp = currenttemp
    basic.pause(1000)
})
// =====================
// ADAPTIVE LOGGING LOOP
// =====================
basic.forever(function () {
    datalogger.log(
    datalogger.createCV("temperature", currenttemp),
    datalogger.createCV("light", light2),
    datalogger.createCV("rolling baseline", Math.round(rollingAvg)),
    datalogger.createCV("dynamic threshold", Math.round(dynamicThreshold)),
    datalogger.createCV("warning margin", warningMargin),
    datalogger.createCV("fire risk", fireRisk),
    datalogger.createCV("log interval ms", logInterval)
    )
    basic.pause(logInterval)
})
