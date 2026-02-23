"""
Wildfire Risk Model — Forest Environmental Monitoring
Leaving Certificate Computer Science 2026
BBC micro:bit Embedded System Project

This model uses data collected from the micro:bit (temperature, light level,
rolling baseline, dynamic threshold, fire risk score) and simulates two
what-if scenarios to predict how wildfire risk changes under different
environmental conditions.
"""

import csv
import os
import random
import math

# ─────────────────────────────────────────────────────────
# SECTION 1: LOAD OR SIMULATE MICROBIT DATA
# The micro:bit logs data to a CSV. If that file is present
# we use it. Otherwise we generate realistic simulated data.
# ─────────────────────────────────────────────────────────

DATAFILE = "microbit_log.csv"

def generate_simulated_data(n=120):
    """
    Generate n simulated readings that mimic a typical day cycle.
    Temperature rises through the morning, peaks midday, then falls.
    Light follows a similar pattern.
    """
    data = []
    for i in range(n):
        hour = (i / n) * 24  # simulate 24 hours across all readings

        # Base temperature follows a sine curve: cooler at night, warmer midday
        base_temp = 15 + 10 * math.sin(math.pi * (hour - 6) / 12)
        # Add small random noise
        temp = round(base_temp + random.uniform(-1.5, 1.5), 1)

        # Light follows sun position: 0 at night, peaks midday
        if 6 <= hour <= 20:
            light = int(100 + 155 * math.sin(math.pi * (hour - 6) / 14))
        else:
            light = random.randint(0, 20)

        data.append({
            "reading": i + 1,
            "temperature": temp,
            "light": light,
        })
    return data


def load_microbit_data():
    """Load data from micro:bit CSV log if it exists, else simulate."""
    if os.path.exists(DATAFILE):
        rows = []
        with open(DATAFILE, newline="") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                try:
                    rows.append({
                        "reading": i + 1,
                        "temperature": float(row.get("temperature", row.get("temperature value", 0))),
                        "light": int(float(row.get("light", row.get("light value", 0)))),
                    })
                except ValueError:
                    continue
        if rows:
            print(f"Loaded {len(rows)} readings from {DATAFILE}")
            return rows
    print("No micro:bit data file found — using simulated data (120 readings, 24-hour cycle)")
    return generate_simulated_data(120)


# ─────────────────────────────────────────────────────────
# SECTION 2: THE ADAPTIVE WILDFIRE RISK MODEL
# Mirrors the logic running on the micro:bit but extended
# to process a full dataset and track how risk evolves.
# ─────────────────────────────────────────────────────────

def run_model(data, temp_offset=0, light_multiplier=1.0, label="Baseline", freeze_baseline=False):
    """
    Run the adaptive wildfire risk model over a dataset.

    Parameters:
        data             — list of {reading, temperature, light} dicts
        temp_offset      — add this to every temperature reading (what-if: hotter climate)
        light_multiplier — multiply every light reading (what-if: longer/more intense sun)
        label            — name for this scenario

    Returns a list of result dicts with risk scores and model state per reading.
    """
    if not data:
        return []

    # Initialise the adaptive model state.
    # freeze_baseline: keep rolling avg fixed so we see raw impact of scenario.
    rolling_avg = data[0]["temperature"]  # always start from real baseline
    warning_margin = 5
    critical_margin = 10
    alert_count = 0
    all_clear_count = 0

    results = []
    total_risk = 0
    critical_events = 0
    high_light_events = 0

    for row in data:
        temp = row["temperature"] + temp_offset
        light = min(255, int(row["light"] * light_multiplier))

        # Update rolling average (exponential moving average)
        # If freeze_baseline, the avg doesn't update — models sudden unexpected event
        if not freeze_baseline:
            rolling_avg = rolling_avg * 0.9 + temp * 0.1

        # Recalculate dynamic thresholds from baseline
        warning_threshold = rolling_avg + warning_margin
        critical_threshold = rolling_avg + critical_margin

        # Score fire risk (0–4)
        risk = 0
        if temp > rolling_avg + 2:
            risk += 1
        if temp > warning_threshold:
            risk += 1
        if temp > critical_threshold:
            risk += 1
        if light > 170:
            risk += 1
            high_light_events += 1

        # Adapt margins based on sustained conditions
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
            "reading": row["reading"],
            "temperature": round(temp, 1),
            "light": light,
            "rolling_avg": round(rolling_avg, 1),
            "warning_threshold": round(warning_threshold, 1),
            "fire_risk": risk,
            "warning_margin": warning_margin,
            "alert_count": alert_count,
        })

    avg_risk = total_risk / len(data) if data else 0

    # Summary
    summary = {
        "label": label,
        "readings": len(data),
        "avg_risk": round(avg_risk, 2),
        "critical_events": critical_events,
        "high_light_events": high_light_events,
        "peak_risk": max(r["fire_risk"] for r in results),
        "peak_temp": max(r["temperature"] for r in results),
        "final_warning_margin": results[-1]["warning_margin"] if results else warning_margin,
    }

    return results, summary


# ─────────────────────────────────────────────────────────
# SECTION 3: WHAT-IF SCENARIOS
# ─────────────────────────────────────────────────────────

def print_separator(char="─", width=60):
    print(char * width)

def print_summary(summary):
    print(f"\n  Scenario:            {summary['label']}")
    print(f"  Readings processed:  {summary['readings']}")
    print(f"  Average risk score:  {summary['avg_risk']} / 4")
    print(f"  Critical events:     {summary['critical_events']}  (risk ≥ 3)")
    print(f"  High light events:   {summary['high_light_events']}  (light > 170)")
    print(f"  Peak temperature:    {summary['peak_temp']}°C")
    print(f"  Peak risk score:     {summary['peak_risk']} / 4")
    print(f"  Final warning margin:{summary['final_warning_margin']}°C  (adapted from 5°C)")

def risk_label(score):
    return ["Safe", "Low", "Moderate", "High", "Critical"][min(score, 4)]

def compare_summaries(baseline, scenario, scenario_name):
    print(f"\n  📊 Impact of '{scenario_name}' vs Baseline:")
    avg_change = scenario["avg_risk"] - baseline["avg_risk"]
    crit_change = scenario["critical_events"] - baseline["critical_events"]
    temp_change = scenario["peak_temp"] - baseline["peak_temp"]
    print(f"     Average risk change:    {avg_change:+.2f}")
    print(f"     Critical events change: {crit_change:+d}")
    print(f"     Peak temperature:       {scenario['peak_temp']}°C  (was {baseline['peak_temp']}°C, Δ {temp_change:+.1f}°C)")


# ─────────────────────────────────────────────────────────
# SECTION 4: SAVE RESULTS TO CSV
# ─────────────────────────────────────────────────────────

def save_results(results, filename):
    if not results:
        return
    fieldnames = results[0].keys()
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n  Results saved to: {filename}")


# ─────────────────────────────────────────────────────────
# MAIN — Run all three scenarios and compare
# ─────────────────────────────────────────────────────────

def main():
    print_separator("═")
    print("  WILDFIRE RISK MODEL — Forest Environmental Monitoring")
    print("  Leaving Certificate Computer Science 2026")
    print_separator("═")

    # Load data from micro:bit or simulate
    data = load_microbit_data()
    print(f"  Total readings: {len(data)}")

    print_separator()

    # ── SCENARIO 0: Baseline (actual collected data, no changes)
    print("\n[SCENARIO 0] BASELINE — Actual micro:bit data, no modifications")
    baseline_results, baseline_summary = run_model(data, temp_offset=0, light_multiplier=1.0, label="Baseline")
    print_summary(baseline_summary)
    save_results(baseline_results, "results_baseline.csv")

    print_separator()

    # ── SCENARIO 1: What if temperature increases by 8°C suddenly?
    # freeze_baseline=True models a sudden unexpected heatwave — the system
    # hasn't had time to recalibrate, so the raw danger is fully visible.
    # This is the more realistic "disaster" scenario.
    print("\n[SCENARIO 1] WHAT-IF: Sudden temperature increase of +8°C")
    print("  (Simulates: sudden heatwave / climate shock — baseline not yet adapted)")
    s1_results, s1_summary = run_model(
        data,
        temp_offset=8,
        light_multiplier=1.0,
        label="Heatwave (+8°C, sudden)",
        freeze_baseline=True
    )
    print_summary(s1_summary)
    compare_summaries(baseline_summary, s1_summary, "Heatwave +8°C")
    save_results(s1_results, "results_scenario1_heatwave.csv")

    print_separator()

    # ── SCENARIO 2: What if light intensity increases by 40%?
    # This simulates deforestation / canopy loss — more direct sunlight
    # reaching the forest floor, drying conditions and increasing fire risk.
    print("\n[SCENARIO 2] WHAT-IF: Light intensity increases by 40%")
    print("  (Simulates: canopy loss / deforestation — more direct sun exposure)")
    s2_results, s2_summary = run_model(
        data,
        temp_offset=0,
        light_multiplier=1.4,
        label="Canopy Loss (light ×1.4)"
    )
    print_summary(s2_summary)
    compare_summaries(baseline_summary, s2_summary, "Canopy Loss +40% light")
    save_results(s2_results, "results_scenario2_canopy_loss.csv")

    print_separator()

    # ── COMBINED SCENARIO: Both heatwave + canopy loss
    print("\n[BONUS] COMBINED: Heatwave +8°C AND canopy loss +40% light")
    print("  (Worst-case: drought + deforestation together)")
    sc_results, sc_summary = run_model(
        data,
        temp_offset=8,
        light_multiplier=1.4,
        label="Combined worst-case",
        freeze_baseline=True
    )
    print_summary(sc_summary)
    compare_summaries(baseline_summary, sc_summary, "Combined worst-case")
    save_results(sc_results, "results_scenario_combined.csv")

    print_separator("═")
    print("\n  FINAL COMPARISON TABLE")
    print_separator()
    print(f"  {'Scenario':<30} {'Avg Risk':>10} {'Critical':>10} {'Peak Temp':>12}")
    print_separator()
    for s in [baseline_summary, s1_summary, s2_summary, sc_summary]:
        print(f"  {s['label']:<30} {s['avg_risk']:>10.2f} {s['critical_events']:>10} {s['peak_temp']:>11.1f}°C")
    print_separator("═")
    print("\n  Output files written:")
    print("    results_baseline.csv")
    print("    results_scenario1_heatwave.csv")
    print("    results_scenario2_canopy_loss.csv")
    print("    results_scenario_combined.csv")
    print("\n  Done.")


if __name__ == "__main__":
    main()