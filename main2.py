 
# readings collected from the microbit datalogger
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
 

# temp_offset adds extra degrees (used for heatwave scenario)
# light_boost makes the light stronger (used for canopy loss scenario)
def run_model(readings, temp_offset=0, light_boost=1.0, label="Baseline"):
 
    # start the rolling average at the first temperature
    rolling_avg = readings[0]["temp"]
 
    # warning margin - how far above normal before we flag a warning
    # this can change over time depending on conditions
    warning_margin = 5
 
    total_risk = 0
    critical_count = 0
 
    print("--- " + label + " ---")
 
    for i in range(len(readings)):
 
        # get this reading and apply any scenario changes
        temp = readings[i]["temp"] + temp_offset
        light = readings[i]["light"] * light_boost
        if light > 255:
            light = 255
 
        # update rolling average - old average counts 90%, new reading counts 10%
        rolling_avg = rolling_avg * 0.9 + temp * 0.1
 
        # warning threshold is rolling average plus the margin
        warning_threshold = rolling_avg + warning_margin
 
        # work out fire risk score (0 to 4)
        risk = 0
 
        if temp > rolling_avg + 2:
            risk = risk + 1   # warmer than normal
 
        if temp > warning_threshold:
            risk = risk + 1   # above warning level
 
        if temp > warning_threshold + 5:
            risk = risk + 1   # extreme heat
 
        if light > 170:
            risk = risk + 1   # bright sun means dry conditions
 
        # adapt the warning margin based on conditions
        if risk >= 3 and warning_margin > 2:
            warning_margin = warning_margin - 1   # tighten up if its been hot
 
        if risk == 0 and warning_margin < 7:
            warning_margin = warning_margin + 1   # relax if its been calm
 
        total_risk = total_risk + risk
 
        if risk >= 3:
            critical_count = critical_count + 1
 
        print("Reading " + str(i + 1) + ":  Temp=" + str(temp) + "  Light=" + str(int(light)) + "  Avg=" + str(round(rolling_avg, 1)) + "  Risk=" + str(risk))
 
    avg_risk = total_risk / len(readings)
 
    print("Average risk: " + str(round(avg_risk, 2)) + " out of 4")
    print("Critical readings (risk 3 or higher): " + str(critical_count))
    print("")
 
 
# run the baseline - normal conditions
run_model(readings, label="Baseline")
 
# scenario 1 - heatwave, add 8 degrees to every reading
run_model(readings, temp_offset=8, label="Heatwave +8C")
 
# scenario 2 - canopy loss from deforestation, light is 40% stronger
run_model(readings, light_boost=1.4, label="Canopy Loss")
