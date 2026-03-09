import csv

readings = [
    {"temp": 20, "light": 100},
    {"temp": 21, "light": 110},
    {"temp": 22, "light": 130},
    {"temp": 24, "light": 160},
    {"temp": 28, "light": 200},
    {"temp": 30, "light": 210},
    {"temp": 29, "light": 180},
    {"temp": 25, "light": 150},
    {"temp": 22, "light": 120},
    {"temp": 20, "light": 100},
]


# --- STEP 2: DEFINE THE MODEL FUNCTION ---
# This function takes the readings and works out the fire risk.
# temp_offset  = adds extra heat (used for heatwave scenario)
# light_boost  = multiplies light level (used for canopy loss scenario)

def run_model(readings, temp_offset=0, light_boost=1.0, label="Baseline"):

    # The rolling average starts at the first temperature reading.
    # It will slowly update each cycle to track what "normal" feels like.
    rolling_avg = readings[0]["temp"]

    # The warning margin controls how far above normal = danger.
    # It starts at 5 degrees and can tighten or relax over time.
    warning_margin = 5

    total_risk = 0       # We'll add up all the risk scores
    critical_count = 0   # Count how many readings hit risk level 3+

    # Store per-reading results so we can write them to CSV later
    results = []

    # Simulate time in seconds — each reading is ~3 seconds apart,
    # matching the 3-second logging interval on the micro:bit
    time_seconds = 0.0

    print("\n--- " + label + " ---")
    print(f"{'Read':>4}  {'Temp':>5}  {'Light':>5}  {'Avg':>5}  {'Risk':>4}")

    for i, row in enumerate(readings):

        # Apply any scenario adjustments to this reading
        temp = row["temp"] + temp_offset
        light = min(255, int(row["light"] * light_boost))

        # Update the rolling average using an exponential moving average.
        # This means it slowly drifts toward the current temperature.
        # Old average matters 90%, new reading matters 10%.
        rolling_avg = rolling_avg * 0.9 + temp * 0.1

        # The warning threshold is the rolling average plus the margin.
        # If today is warmer than usual by this much, that's a warning.
        warning_threshold = rolling_avg + warning_margin

        # --- CALCULATE FIRE RISK (0 to 4) ---
        risk = 0

        if temp > rolling_avg + 2:       # Warmer than recent normal
            risk += 1
        if temp > warning_threshold:     # Above warning level
            risk += 1
        if temp > warning_threshold + 5: # Extreme heat
            risk += 1
        if light > 170:                  # Bright sun = dry conditions
            risk += 1

        # --- ADAPT THE WARNING MARGIN ---
        # If risk has been high for a while, tighten the margin (more sensitive).
        # If conditions are calm, relax the margin back toward normal.
        if risk >= 3 and warning_margin > 2:
            warning_margin -= 1   # become more alert
        elif risk == 0 and warning_margin < 7:
            warning_margin += 1   # relax back to normal

        # Keep a running total and count critical events
        total_risk += risk
        if risk >= 3:
            critical_count += 1

        # Print this reading's results in a simple table
        print(f"{i+1:>4}  {temp:>5.1f}  {light:>5}  {rolling_avg:>5.1f}  {risk:>4}")

        # Save this row for CSV export
        results.append({
            "time (seconds)": round(time_seconds, 3),
            "light value":    light,
            "temperature value": temp
        })

        # Advance simulated time by 3 seconds per reading
        time_seconds += 3.0

    # Work out the average risk across all readings
    avg_risk = total_risk / len(readings)

    print(f"\n  Average risk: {avg_risk:.2f} / 4")
    print(f"  Critical events (risk 3+): {critical_count}")

    # --- WRITE CSV ---
    # File is named after the scenario label, spaces replaced with underscores
    filename = label.replace(" ", "_") + ".csv"
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["time (seconds)", "light value", "temperature value"])
        writer.writeheader()
        writer.writerows(results)

    print(f"  CSV saved → {filename}")

    return results


# --- STEP 3: RUN THREE SCENARIOS ---

# Scenario A: Normal conditions (no changes)
run_model(readings, label="Baseline")

# Scenario B: Sudden heatwave — add 8 degrees to every reading
run_model(readings, temp_offset=8, label="Heatwave +8C")

# Scenario C: Canopy loss (deforestation) — light is 40% brighter
run_model(readings, light_boost=1.4, label="Canopy Loss (light x1.4)")
