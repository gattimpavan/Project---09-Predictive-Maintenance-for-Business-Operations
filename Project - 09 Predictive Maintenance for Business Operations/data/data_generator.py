"""
Siemens AG - Predictive Maintenance Telemetry Data Generator
Project - 09: Predictive Maintenance for Business Operations

Synthesizes high-fidelity industrial IoT sensor streams, maintenance logs,
and MES production schedule data across 50 Siemens machines in 5 global plants:
- Sensor Streams: Vibration RMS, Peak Accel, Bearing Temp, Motor Temp, Lube Oil Pressure,
  Oil Particle Count, Acoustic Emission, Electrical Load, Rotational Speed, Tool Wear Index.
- Maintenance History: Operating hours since PM, Lifetime hours, MTBF, MTTR, Past failures,
  Technician qualification, Component health score.
- Production Schedule: Shift load, Job orders, Batch priority tiers, Scheduled downtime windows,
  Hourly downtime cost ($150k - $420k/hr).
- Ground Truth Labels: Failure occurrence, Multi-class failure patterns, Remaining Useful Life (RUL).
"""

import os
import json
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set deterministic random seeds
np.random.seed(42)
random.seed(42)

# Siemens Global Manufacturing Plants
PLANTS = [
    {
        "plant_id": "DE-ERL-01",
        "plant_name": "Siemens Electronics Works Erlangen",
        "location": "Erlangen, Germany",
        "specialty": "High-Precision CNC & Drive Inverter Assembly",
        "base_downtime_cost_hr": 240000
    },
    {
        "plant_id": "DE-AMB-02",
        "plant_name": "Siemens Digital Enterprise Amberg",
        "location": "Amberg, Germany",
        "specialty": "Simatic PLC & Edge Computing Automated Lines",
        "base_downtime_cost_hr": 310000
    },
    {
        "plant_id": "DE-BER-03",
        "plant_name": "Siemens Gas Turbine Works Berlin",
        "location": "Berlin, Germany",
        "specialty": "Heavy Industrial Gas & Steam Turbines (SGT-800)",
        "base_downtime_cost_hr": 420000
    },
    {
        "plant_id": "DE-NUR-04",
        "plant_name": "Siemens Large Drives Plant Nuremberg",
        "location": "Nuremberg, Germany",
        "specialty": "High-Voltage Simotics Induction Motors & Generators",
        "base_downtime_cost_hr": 280000
    },
    {
        "plant_id": "DE-KAR-05",
        "plant_name": "Siemens Process Automation Works Karlsruhe",
        "location": "Karlsruhe, Germany",
        "specialty": "Centrifugal Process Compressors & Turbomachinery",
        "base_downtime_cost_hr": 350000
    }
]

# Siemens Asset Types and Nominal Operating Specifications
ASSET_TYPES = [
    {
        "type_id": "CNC_MILL",
        "model_name": "Siemens Sinumerik 840D High-Speed 5-Axis Mill",
        "nominal_rpm": 12000,
        "nominal_vib_rms": 1.4,
        "nominal_temp": 52.0,
        "nominal_pressure": 5.2,
        "nominal_load": 72.0,
        "mtbf_mean": 1400
    },
    {
        "type_id": "GAS_TURBINE",
        "model_name": "Siemens SGT-800 Heavy Industrial Gas Turbine",
        "nominal_rpm": 6600,
        "nominal_vib_rms": 2.1,
        "nominal_temp": 78.0,
        "nominal_pressure": 5.8,
        "nominal_load": 85.0,
        "mtbf_mean": 2200
    },
    {
        "type_id": "HV_MOTOR",
        "model_name": "Siemens Simotics HV Series High-Voltage Motor",
        "nominal_rpm": 3000,
        "nominal_vib_rms": 1.2,
        "nominal_temp": 58.0,
        "nominal_pressure": 4.9,
        "nominal_load": 78.0,
        "mtbf_mean": 1800
    },
    {
        "type_id": "ROBOTIC_CELL",
        "model_name": "Siemens Automated 6-Axis Robotic Welding Cell",
        "nominal_rpm": 1800,
        "nominal_vib_rms": 1.1,
        "nominal_temp": 46.0,
        "nominal_pressure": 4.5,
        "nominal_load": 65.0,
        "mtbf_mean": 1600
    },
    {
        "type_id": "COMPRESSOR",
        "model_name": "Siemens STC-SV Multi-Stage Centrifugal Compressor",
        "nominal_rpm": 8500,
        "nominal_vib_rms": 1.8,
        "nominal_temp": 64.0,
        "nominal_pressure": 6.2,
        "nominal_load": 82.0,
        "mtbf_mean": 2000
    }
]

FAILURE_PATTERNS = [
    "No_Failure",
    "Bearing_Degradation",
    "Thermal_Runaway",
    "Power_Electrical_Fault",
    "Tool_Wear_Exhaustion",
    "Lubrication_Breakdown"
]

def generate_siemens_fleet_directory():
    """Generates the master metadata directory for 50 Siemens machines."""
    machines = []
    machine_idx = 1
    
    for plant in PLANTS:
        # 10 machines per plant
        for i in range(10):
            asset_type = ASSET_TYPES[i % len(ASSET_TYPES)]
            m_id = f"SMN-{plant['plant_id'].split('-')[1]}-{machine_idx:03d}"
            
            # Baseline health status
            rand_val = np.random.rand()
            if rand_val < 0.70:
                health_status = "Optimal"
            elif rand_val < 0.88:
                health_status = "Warning"
            else:
                health_status = "Critical"
                
            lifetime_hours = int(np.random.uniform(5000, 48000))
            hours_since_pm = int(np.random.uniform(50, 3200))
            
            machines.append({
                "machine_id": m_id,
                "machine_name": f"{asset_type['model_name']} #{i+1}",
                "asset_type_id": asset_type["type_id"],
                "asset_model": asset_type["model_name"],
                "plant_id": plant["plant_id"],
                "plant_name": plant["plant_name"],
                "location": plant["location"],
                "installation_year": 2026 - int(lifetime_hours / 6000),
                "cumulative_lifetime_hours": lifetime_hours,
                "hours_since_last_pm": hours_since_pm,
                "health_status": health_status,
                "criticality_tier": "Tier 1 (High Impact)" if i < 4 else ("Tier 2 (Medium Impact)" if i < 8 else "Tier 3 (Standard)"),
                "downtime_cost_per_hour_usd": plant["base_downtime_cost_hr"] + int(np.random.uniform(-30000, 50000)),
                "nominal_rpm": asset_type["nominal_rpm"],
                "nominal_vib_rms": asset_type["nominal_vib_rms"],
                "nominal_temp": asset_type["nominal_temp"],
                "nominal_pressure": asset_type["nominal_pressure"],
                "nominal_load": asset_type["nominal_load"],
                "historical_mtbf_hours": asset_type["mtbf_mean"] + int(np.random.uniform(-200, 300)),
                "historical_mttr_hours": round(np.random.uniform(3.5, 9.5), 1)
            })
            machine_idx += 1
            
    return pd.DataFrame(machines)

def generate_predictive_maintenance_dataset(num_records=15000, output_dir=None):
    """
    Generates 15,000 multi-stream operational telemetry records
    linking physical sensors, maintenance history, and MES production scheduling.
    """
    fleet_df = generate_siemens_fleet_directory()
    machines = fleet_df.to_dict(orient="records")
    
    start_time = datetime(2026, 7, 1, 0, 0, 0)
    records = []
    
    shifts = ["Shift A (Morning)", "Shift B (Evening)", "Shift C (Night)"]
    batch_priorities = ["Tier 1 (Urgent/Penalized)", "Tier 2 (Standard Contract)", "Tier 3 (Buffer Run)"]
    
    for idx in range(num_records):
        machine = random.choice(machines)
        record_time = start_time + timedelta(minutes=int(idx * 8.64))
        
        # Operational context
        shift = random.choice(shifts)
        priority = np.random.choice(batch_priorities, p=[0.30, 0.50, 0.20])
        order_id = f"JOB-SMN-{np.random.randint(10000, 99999)}"
        scheduled_units = int(np.random.uniform(150, 600))
        hours_to_next_window = round(float(np.random.exponential(scale=24.0) + 2.0), 1)
        hours_to_next_window = min(hours_to_next_window, 120.0)
        
        # Degradation progression factor
        pm_hours = machine["hours_since_last_pm"] + (idx % 400)
        wear_ratio = min(pm_hours / float(machine["historical_mtbf_hours"]), 1.8)
        
        # Probability of impending failure increases non-linearly with wear and fatigue
        failure_prob_base = 0.08 + (0.35 * (wear_ratio ** 2.2))
        failure_prob = min(max(failure_prob_base + np.random.normal(0, 0.04), 0.02), 0.95)
        
        # Determine if this operating record captures a failure pattern
        is_failure = 1 if np.random.rand() < failure_prob else 0
        
        if is_failure == 0:
            pattern = "No_Failure"
            rul_hours = float(np.random.uniform(140.0, 650.0))
            
            vib_rms = max(machine["nominal_vib_rms"] + np.random.normal(0, 0.25), 0.5)
            vib_peak = max(vib_rms * np.random.uniform(1.3, 1.8), 0.8)
            bearing_temp = max(machine["nominal_temp"] + np.random.normal(0, 3.5), 35.0)
            motor_temp = bearing_temp + np.random.uniform(3.0, 8.0)
            lube_pressure = max(machine["nominal_pressure"] + np.random.normal(0, 0.22), 3.8)
            oil_particles = int(np.random.uniform(15, 60))
            acoustic_db = max(45.0 + np.random.normal(0, 4.0), 38.0)
            elec_load = min(max(machine["nominal_load"] + np.random.normal(0, 4.5), 50.0), 95.0)
            speed_rpm = machine["nominal_rpm"] * np.random.uniform(0.985, 1.015)
            tool_wear_pct = min(wear_ratio * 45.0 + np.random.uniform(0, 10), 75.0)
            
        else:
            # Imminent failure mode assigned based on physics characteristics
            pattern_choices = [
                "Bearing_Degradation",
                "Thermal_Runaway",
                "Power_Electrical_Fault",
                "Tool_Wear_Exhaustion",
                "Lubrication_Breakdown"
            ]
            pattern = np.random.choice(pattern_choices, p=[0.32, 0.22, 0.18, 0.14, 0.14])
            
            # Remaining Useful Life is critically short under failure trajectory
            rul_hours = float(np.random.exponential(scale=22.0) + 1.5)
            rul_hours = min(rul_hours, 72.0)
            
            # Physics-based sensor perturbation by failure mode
            if pattern == "Bearing_Degradation":
                # Spalling, cage damage: high vibration velocity and sharp peak accelerations
                vib_rms = machine["nominal_vib_rms"] + np.random.uniform(3.8, 8.5)
                vib_peak = vib_rms * np.random.uniform(2.4, 4.2)
                bearing_temp = machine["nominal_temp"] + np.random.uniform(18.0, 38.0)
                motor_temp = bearing_temp - np.random.uniform(4.0, 10.0)
                lube_pressure = machine["nominal_pressure"] - np.random.uniform(0.3, 0.9)
                oil_particles = int(np.random.uniform(160, 480))
                acoustic_db = float(np.random.uniform(72.0, 94.0))
                elec_load = machine["nominal_load"] + np.random.uniform(8.0, 22.0)
                speed_rpm = machine["nominal_rpm"] * np.random.uniform(0.94, 0.99)
                tool_wear_pct = min(np.random.uniform(40.0, 85.0), 98.0)
                
            elif pattern == "Thermal_Runaway":
                # Heat dissipation collapse, coolant failure
                vib_rms = machine["nominal_vib_rms"] + np.random.uniform(1.2, 3.2)
                vib_peak = vib_rms * np.random.uniform(1.4, 2.2)
                bearing_temp = machine["nominal_temp"] + np.random.uniform(32.0, 58.0)
                motor_temp = bearing_temp + np.random.uniform(12.0, 28.0)
                lube_pressure = machine["nominal_pressure"] - np.random.uniform(0.8, 1.8)
                oil_particles = int(np.random.uniform(80, 220))
                acoustic_db = float(np.random.uniform(62.0, 80.0))
                elec_load = machine["nominal_load"] + np.random.uniform(14.0, 35.0)
                speed_rpm = machine["nominal_rpm"] * np.random.uniform(0.92, 0.98)
                tool_wear_pct = min(np.random.uniform(45.0, 90.0), 99.0)
                
            elif pattern == "Power_Electrical_Fault":
                # Stator phase imbalance, harmonic overload, inverter failure
                vib_rms = machine["nominal_vib_rms"] + np.random.uniform(2.0, 4.5)
                vib_peak = vib_rms * np.random.uniform(1.6, 2.5)
                bearing_temp = machine["nominal_temp"] + np.random.uniform(8.0, 20.0)
                motor_temp = bearing_temp + np.random.uniform(18.0, 36.0)
                lube_pressure = machine["nominal_pressure"] + np.random.normal(0, 0.3)
                oil_particles = int(np.random.uniform(25, 80))
                acoustic_db = float(np.random.uniform(68.0, 88.0))
                elec_load = machine["nominal_load"] + np.random.uniform(28.0, 58.0) # major current spike
                speed_rpm = machine["nominal_rpm"] * np.random.uniform(0.88, 1.05) # speed oscillation
                tool_wear_pct = min(np.random.uniform(30.0, 70.0), 95.0)
                
            elif pattern == "Tool_Wear_Exhaustion":
                # Excessive flank/crater wear, micro-chipping on cutting edges
                vib_rms = machine["nominal_vib_rms"] + np.random.uniform(2.5, 5.0)
                vib_peak = vib_rms * np.random.uniform(2.0, 3.5)
                bearing_temp = machine["nominal_temp"] + np.random.uniform(6.0, 16.0)
                motor_temp = bearing_temp + np.random.uniform(2.0, 8.0)
                lube_pressure = machine["nominal_pressure"] - np.random.uniform(0.1, 0.4)
                oil_particles = int(np.random.uniform(90, 260))
                acoustic_db = float(np.random.uniform(76.0, 96.0)) # high screeching acoustic
                elec_load = machine["nominal_load"] + np.random.uniform(12.0, 26.0) # spindle motor dragging
                speed_rpm = machine["nominal_rpm"] * np.random.uniform(0.93, 0.99)
                tool_wear_pct = float(np.random.uniform(88.0, 100.0)) # critical tool wear
                
            else: # Lubrication_Breakdown
                # Oil viscosity loss, dry boundary friction, pump cavitation
                vib_rms = machine["nominal_vib_rms"] + np.random.uniform(2.2, 5.5)
                vib_peak = vib_rms * np.random.uniform(1.8, 3.0)
                bearing_temp = machine["nominal_temp"] + np.random.uniform(22.0, 44.0)
                motor_temp = bearing_temp + np.random.uniform(5.0, 15.0)
                lube_pressure = max(machine["nominal_pressure"] - np.random.uniform(1.6, 3.2), 1.2) # severe pressure drop
                oil_particles = int(np.random.uniform(220, 650)) # massive wear particulates
                acoustic_db = float(np.random.uniform(70.0, 91.0))
                elec_load = machine["nominal_load"] + np.random.uniform(8.0, 20.0)
                speed_rpm = machine["nominal_rpm"] * np.random.uniform(0.95, 0.99)
                tool_wear_pct = min(np.random.uniform(40.0, 80.0), 95.0)
                
        # Component health score (0-100)
        health_score = max(min(100.0 - (vib_rms * 4.2) - (bearing_temp * 0.35) + (lube_pressure * 3.5) - (oil_particles * 0.04), 100.0), 5.0)
        
        # Historical metrics
        past_failures = int(np.random.poisson(lam=1.6))
        tech_grade = int(np.random.choice([1, 2, 3, 4], p=[0.20, 0.35, 0.30, 0.15]))
        
        records.append({
            "record_id": f"REC-SMN-{idx+1:06d}",
            "timestamp": record_time.strftime("%Y-%m-%d %H:%M:%S"),
            "machine_id": machine["machine_id"],
            "machine_name": machine["machine_name"],
            "asset_type_id": machine["asset_type_id"],
            "plant_id": machine["plant_id"],
            "plant_name": machine["plant_name"],
            "criticality_tier": machine["criticality_tier"],
            "downtime_cost_per_hour_usd": machine["downtime_cost_per_hour_usd"],
            # Sensor Streams
            "vibration_rms_mm_s": round(vib_rms, 2),
            "vibration_peak_accel_g": round(vib_peak, 2),
            "bearing_temp_celsius": round(bearing_temp, 1),
            "motor_casing_temp_celsius": round(motor_temp, 1),
            "lube_oil_pressure_bar": round(lube_pressure, 2),
            "oil_particle_count_ppm": oil_particles,
            "acoustic_emission_db": round(acoustic_db, 1),
            "electrical_current_load_pct": round(elec_load, 1),
            "rotational_speed_rpm": int(speed_rpm),
            "tool_wear_index_pct": round(tool_wear_pct, 1),
            # Maintenance History
            "operating_hours_since_pm": pm_hours,
            "cumulative_lifetime_hours": machine["cumulative_lifetime_hours"] + pm_hours,
            "historical_mtbf_hours": machine["historical_mtbf_hours"],
            "historical_mttr_hours": machine["historical_mttr_hours"],
            "past_failure_count": past_failures,
            "technician_qualification_level": tech_grade,
            "component_health_score": round(health_score, 1),
            # MES Production Schedule
            "active_production_shift": shift,
            "batch_priority_tier": priority,
            "job_order_id": order_id,
            "scheduled_shift_units": scheduled_units,
            "hours_to_next_maintenance_window": hours_to_next_window,
            # Target Labels
            "failure_occurred": is_failure,
            "failure_pattern": pattern,
            "remaining_useful_life_hrs": round(rul_hours, 1)
        })
        
    df = pd.DataFrame(records)
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        csv_file = os.path.join(output_dir, "siemens_predictive_maintenance_telemetry.csv")
        fleet_file = os.path.join(output_dir, "siemens_machines_directory.csv")
        
        df.to_csv(csv_file, index=False)
        fleet_df.to_csv(fleet_file, index=False)
        print(f"[DataGen] Successfully saved {len(df):,} telemetry records to {csv_file}")
        print(f"[DataGen] Successfully saved {len(fleet_df)} machine fleet records to {fleet_file}")
        
    return df, fleet_df

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    generate_predictive_maintenance_dataset(num_records=15000, output_dir=current_dir)

