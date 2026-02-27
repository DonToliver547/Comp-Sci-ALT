# Wildfire Risk Model - Forest Environmental Monitoring
# Leaving Certificate Computer Science 2026
# BBC micro:bit Embedded System Project

import math
import csv



# SECTION 1: GET USER INPUT


def get_float(prompt, min_val=None, max_val=None):
    while True:
        try:
            val = float(input(prompt))
            if min_val is not None and val < min_val:
                print("  Value must be at least " + str(min_val) + ". Try again.")
                continue
            if max_val is not None and val > max_val:
                print("  Value must be at most " + str(max_val) + ". Try again.")
                continue
            return val
        except ValueError:
            print("  Please enter a valid number.")

def get_int(prompt, min_val=None, max_val=None):
    while True:
        try:
            val = int(input(prompt))
            if min_val is not None and val < min_val:
                print("  Value must be at least " + str(min_val) + ". Try again.")
                continue
            if max_val is not None and val > max_val:
                print("  Value must be at most " + str(max_val) + ". Try again.")
                continue
            return val
        except ValueError:
            print("  Please enter a whole number.")

def collect_user_inputs():
    print("-" * 60)
    print("  ENTER YOUR MICRO:BIT SENSOR READINGS")
    print("-" * 60)

    print("\n  --- Temperature Readings (degrees C) ---")
    peak_temp       = get_float("  Peak (highest) temperature recorded: ")
    low_temp        = get_float("  Lowest temperature recorded: ", max_val=peak_temp)
    start_temp      = get_float("  Starting temperature (first reading): ", min_val=low_temp, max_val=peak_temp)
    max_temp_change = get_float("  Largest single-cycle temperature change (degrees C, e.g. 3.5): ", min_val=0)

    print("\n  --- Light Level Readings (0-255) ---")
    peak_light = get_int("  Peak (highest) light level recorded (0-255): ", min_val=0, max_val=255)
    avg_light  = get_int("  Average light level across the session (0-255): ", min_val=0, max_val=peak_light)

    print("\n  --- Session Info ---")
    num_readings = get_int("  Total number of readings logged: ", min_val=1)
    duration_min = get_float("  Session duration in minutes: ", min_val=0.1)

    return {
        "peak_temp":        peak_temp,
        "low_temp":         low_temp,
        "start_temp":       start_temp,
        "max_temp_change":  max_temp_change,
        "peak_light":       peak_light,
        "avg_light":        avg_light,
        "num_readings":     num_readings,
        "duration_min":     duration_min,
    }



# SECTION 2: BUILD DATA SERIES FROM USER INPUTS


def build_data_from_inputs(inputs):
    n       = inputs["num_readings"]
    peak    = inputs["peak_temp"]
    low     = inputs["low_temp"]
    start   = inputs["start_temp"]
    p_light = inputs["peak_light"]
    a_light = inputs["avg_light"]

    data = []
    for i in range(n):
        t = i / max(n - 1, 1)

        mid = (peak + low) / 2
        amp = (peak - low) / 2
        phase_offset = 0.0
        if amp > 0:
            ratio = max(-1.0, min(1.0, (start - mid) / amp))
            phase_offset = math.asin(ratio)
        temp  = round(mid + amp * math.sin(math.pi * t + phase_offset), 1)
        light = int(max(0, min(255, a_light + (p_light - a_light) * math.sin(math.pi * t))))

        data.append({"reading": i + 1, "temperature": temp, "light": light})

    return data



# SECTION 3: ADAPTIVE WILDFIRE RISK MODEL

def run_model(data, temp_offset=0, light_multiplier=1.0, label="Baseline", freeze_baseline=False):
    if not data:
        return [], {}

    rolling_avg       = data[0]["temperature"]
    warning_margin    = 5
    critical_margin   = 10
    alert_count       = 0
    all_clear_count   = 0
    results           = []
    total_risk        = 0
    critical_events   = 0
    high_light_events = 0

    for row in data:
        temp  = row["temperature"] + temp_offset
        light = min(255, int(row["light"] * light_multiplier))

        if not freeze_baseline:
            rolling_avg = rolling_avg * 0.9 + temp * 0.1

        warning_threshold  = rolling_avg + warning_margin
        critical_threshold = rolling_avg + critical_margin

        risk = 0
        if temp > rolling_avg + 2:    risk += 1
        if temp > warning_threshold:  risk += 1
        if temp > critical_threshold: risk += 1
        if light > 170:
            risk += 1
            high_light_events += 1

        if risk >= 3:
            alert_count += 1
            all_clear_count = 0
            if alert_count >= 4 and warning_margin > 2:
                warning_margin -= 1
        elif risk == 0:
            all_clear_count += 1
            alert_count = 0
            if all_clear_count >= 6 and warning_margin < 7:
                warning_margin += 1

        critical_margin = warning_margin + 5
        total_risk += risk
        if risk >= 3:
            critical_events += 1

        results.append({
            "reading":           row["reading"],
            "temperature":       round(temp, 1),
            "light":             light,
            "rolling_avg":       round(rolling_avg, 1),
            "warning_threshold": round(warning_threshold, 1),
            "fire_risk":         risk,
            "warning_margin":    warning_margin,
        })

    avg_risk = total_risk / len(data)

    summary = {
        "label":                label,
        "readings":             len(data),
        "avg_risk":             round(avg_risk, 2),
        "critical_events":      critical_events,
        "high_light_events":    high_light_events,
        "peak_risk":            max(r["fire_risk"] for r in results),
        "peak_temp":            max(r["temperature"] for r in results),
        "final_warning_margin": results[-1]["warning_margin"],
    }

    return results, summary



# SECTION 4: SAVE RESULTS TO CSV


def save_csv(results, filename):
    if not results:
        return
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)



# MAIN


def main():
    inputs = collect_user_inputs()
    data   = build_data_from_inputs(inputs)

    baseline_results, baseline_summary = run_model(
        data, temp_offset=0, light_multiplier=1.0, label="Baseline")

    s1_results, s1_summary = run_model(
        data, temp_offset=8, light_multiplier=1.0,
        label="Heatwave +8C", freeze_baseline=True)

    s2_results, s2_summary = run_model(
        data, temp_offset=0, light_multiplier=1.4,
        label="Canopy Loss light x1.4")

    sc_results, sc_summary = run_model(
        data, temp_offset=8, light_multiplier=1.4,
        label="Combined worst-case", freeze_baseline=True)

    save_csv(baseline_results, "results_baseline.csv")
    save_csv(s1_results,       "results_heatwave.csv")
    save_csv(s2_results,       "results_canopy_loss.csv")
    save_csv(sc_results,       "results_combined.csv")

    print("\n  fire risk score (0 = safe, 4 = critical)")
    print("-" * 60)
    print("  Scenario                         Avg Risk   Critical Events")
    print("-" * 60)
    for s in [baseline_summary, s1_summary, s2_summary, sc_summary]:
        print("  " + s["label"].ljust(32) +
              str(s["avg_risk"]).rjust(8) +
              str(s["critical_events"]).rjust(16))
    print("-" * 60)
    print("\n  CSV files saved:")
    print("    results_baseline.csv")
    print("    results_heatwave.csv")
    print("    results_canopy_loss.csv")
    print("    results_combined.csv")


if __name__ == "__main__":
    main()
