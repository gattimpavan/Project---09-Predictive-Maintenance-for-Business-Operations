"""
Siemens AG - Prescriptive Maintenance & Autonomous Operations Engine
Project - 09: Predictive Maintenance for Business Operations

Translates predictive machine intelligence and production schedule constraints
into 4 Autonomous Prescriptive Maintenance Protocols:
1. Protocol Alpha: Emergency Controlled Halt & High-Priority Replacement
2. Protocol Beta: Dynamic Load Throttling & Production Window Bridging
3. Protocol Gamma: Autonomous Lubrication Flush & Rapid Tooling Reset
4. Protocol Delta: Automated ERP Spare Requisition & Schedule Synchronization
"""

import os
import json
import numpy as np
import pandas as pd

PROTOCOLS = {
    "ALPHA": {
        "code": "PROTOCOL_ALPHA",
        "name": "Emergency Controlled Halt & Spindle Fast-Swap",
        "severity": "CRITICAL_SEVERITY",
        "badge_color": "#FF3366", # Alert Crimson
        "lead_time_required_hrs": 1.5,
        "required_tech_grade": "Grade 4 (Master Specialist)",
        "action_summary": "Immediate automated load de-energization, batch reroute to sibling machine, and emergency component replacement.",
        "operational_steps": [
            "Trigger automated interlock deceleration to prevent catastrophic mechanical crash.",
            "Reroute in-flight MES batch order to redundant sister work-center.",
            "Dispatch Grade-4 Siemens Field Engineer with OEM precision replacement cartridge.",
            "Perform dynamic laser shaft alignment and high-speed vibration baseline calibration."
        ],
        "spare_parts_kit": "OEM Spindle Cartridge / Bearing Housing Assembly Kit (Part #SMN-9842)",
        "expected_mttr_hrs": 4.5
    },
    "BETA": {
        "code": "PROTOCOL_BETA",
        "name": "Dynamic Load Throttling & Window Bridging",
        "severity": "HIGH_SEVERITY",
        "badge_color": "#FFB300", # Warning Amber
        "lead_time_required_hrs": 0.5,
        "required_tech_grade": "Grade 3 (Senior Systems Specialist)",
        "action_summary": "Throttle feed rate / turbine firing rate by 18% to suppress thermal/vibration stress and finish active batch before maintenance window.",
        "operational_steps": [
            "Issue digital override command to Siemens Sinumerik / Simatic PLC reducing spindle load by 18%.",
            "Engage auxiliary high-pressure coolant chiller to maintain bearing temperature below 75°C.",
            "Bridge remaining operational hours until the scheduled shift changeover window.",
            "Conduct targeted condition overhaul during planned 2-hour production interlock."
        ],
        "spare_parts_kit": "High-Pressure Seal Kit & Coolant Valve Restrictor (Part #SMN-6210)",
        "expected_mttr_hrs": 2.2
    },
    "GAMMA": {
        "code": "PROTOCOL_GAMMA",
        "name": "Autonomous Lubrication & Tooling Refresh",
        "severity": "MODERATE_SEVERITY",
        "badge_color": "#00E5FF", # Electric Cyan
        "lead_time_required_hrs": 4.0,
        "required_tech_grade": "Grade 2 (Maintenance Technician)",
        "action_summary": "Automated high-viscosity synthetic lubrication purge and robotic carbide tooling changeover during Shift C buffer.",
        "operational_steps": [
            "Command automated central lubrication manifold to flush micro-particulate debris.",
            "Inject synthetic polyalphaolefin (PAO) high-film-strength lubricant at 5.5 bar.",
            "Index automatic tool changer carousel to fresh multi-layer TiAlN coated carbide inserts.",
            "Verify acoustic emission levels return to nominal baseline (<55 dB)."
        ],
        "spare_parts_kit": "Siemens Precision Lubricant Canister ISO VG 68 & Carbide Inserts (Part #SMN-3389)",
        "expected_mttr_hrs": 1.2
    },
    "DELTA": {
        "code": "PROTOCOL_DELTA",
        "name": "Predictive ERP Requisition & Schedule Sync",
        "severity": "LOW_SEVERITY",
        "badge_color": "#00C853", # Siemens Operational Green
        "lead_time_required_hrs": 24.0,
        "required_tech_grade": "Grade 1 / Automated Procurement",
        "action_summary": "Pre-order long-lead rotating assemblies via Siemens SAP PM EDI and lock scheduled overhaul into upcoming weekend window.",
        "operational_steps": [
            "Generate autonomous SAP PM work order requisition for scheduled bearing set.",
            "Reserve technician allocation in MES scheduling roster for upcoming maintenance window.",
            "Continuous edge telemetry monitoring with tightened adaptive anomaly tripwires.",
            "Zero impact to current production throughput or customer delivery deadlines."
        ],
        "spare_parts_kit": "Standard Scheduled Overhaul Kit & Gasket Pack (Part #SMN-1104)",
        "expected_mttr_hrs": 3.0
    }
}

class PrescriptiveEngine:
    def __init__(self):
        self.protocols = PROTOCOLS

    def formulate_recommendation(self, prediction, operational_context):
        """
        Formulates the optimal maintenance protocol based on ML predictions
        and active MES production schedule constraints.
        """
        fail_prob = prediction["failure_probability"]
        pattern = prediction["diagnosed_pattern"]
        rul_hrs = prediction["predicted_rul_hours"]
        
        hours_to_window = float(operational_context.get("hours_to_next_maintenance_window", 24.0))
        priority_tier = operational_context.get("batch_priority_tier", "Tier 2 (Standard Contract)")
        downtime_cost_hr = float(operational_context.get("downtime_cost_per_hour_usd", 250000))
        
        # Decision Logic:
        # 1. Critical Failure Imminent (RUL < 12h or Risk > 75%)
        if fail_prob >= 0.75 or rul_hrs < 12.0:
            selected_proto = self.protocols["ALPHA"]
            recommendation_rationale = (
                f"Critical failure imminent ({pattern}, RUL: {rul_hrs:.1f}h). Immediate controlled halt "
                f"is mandated to prevent catastrophic spindle/rotor seizure, avoiding an estimated "
                f"${downtime_cost_hr * 4.5:,.0f} in unplanned destruction and collateral damage."
            )
            prevented_downtime_hrs = 18.5
            net_preserved_value = (prevented_downtime_hrs * downtime_cost_hr) - 28000 # minus intervention cost
            
        # 2. Moderate to High Risk with Urgent Batch Running
        elif (fail_prob >= 0.40 or rul_hrs < hours_to_window) and "Tier 1" in priority_tier:
            selected_proto = self.protocols["BETA"]
            recommendation_rationale = (
                f"Elevated risk ({pattern}, RUL: {rul_hrs:.1f}h) during mission-critical Tier-1 production batch. "
                f"Throttling feed/load by 18% extends RUL to {rul_hrs * 1.35:.1f}h, bridging the remaining "
                f"{hours_to_window:.1f}h until the scheduled shift changeover without triggering contract default penalties."
            )
            prevented_downtime_hrs = 12.0
            net_preserved_value = (prevented_downtime_hrs * downtime_cost_hr) - 12000
            
        # 3. Component-Specific Lubrication or Tooling Wear Degradation
        elif pattern in ["Lubrication_Breakdown", "Tool_Wear_Exhaustion"] or (fail_prob >= 0.30 and rul_hrs < 72.0):
            selected_proto = self.protocols["GAMMA"]
            recommendation_rationale = (
                f"Degradation signature diagnosed as {pattern} (RUL: {rul_hrs:.1f}h). Automated lubrication purge "
                f"and carbide insert indexing scheduled for next low-intensity shift buffer, restoring nominal friction coefficients."
            )
            prevented_downtime_hrs = 8.5
            net_preserved_value = (prevented_downtime_hrs * downtime_cost_hr) - 6500
            
        # 4. Early-stage Anomaly / Long RUL
        else:
            selected_proto = self.protocols["DELTA"]
            recommendation_rationale = (
                f"Asset operating within acceptable tolerance with early micro-degradation ({pattern}, RUL: {rul_hrs:.1f}h). "
                f"Autonomous SAP PM requisition generated for next planned quarterly overhaul window. Zero production disturbance."
            )
            prevented_downtime_hrs = 5.0
            net_preserved_value = (prevented_downtime_hrs * downtime_cost_hr) - 3500
            
        return {
            "protocol_code": selected_proto["code"],
            "protocol_name": selected_proto["name"],
            "severity": selected_proto["severity"],
            "badge_color": selected_proto["badge_color"],
            "required_tech_grade": selected_proto["required_tech_grade"],
            "action_summary": selected_proto["action_summary"],
            "operational_steps": selected_proto["operational_steps"],
            "spare_parts_kit": selected_proto["spare_parts_kit"],
            "expected_mttr_hrs": selected_proto["expected_mttr_hrs"],
            "recommendation_rationale": recommendation_rationale,
            "prevented_downtime_hrs": round(prevented_downtime_hrs, 1),
            "net_preserved_value_usd": round(net_preserved_value, 2),
            "roi_ratio": round(net_preserved_value / max(downtime_cost_hr * 0.1, 10000), 1)
        }

    def evaluate_fleet_protocols(self, fleet_df, analyzer):
        """Evaluates prescriptive protocols for all 50 fleet machines."""
        results = []
        for _, machine in fleet_df.iterrows():
            # Build representative input from nominals + current health
            health = machine["health_status"]
            if health == "Critical":
                v_mult = 3.6
                t_mult = 1.45
                p_drop = 1.8
                hours_pm = 3100
            elif health == "Warning":
                v_mult = 2.0
                t_mult = 1.20
                p_drop = 0.8
                hours_pm = 1800
            else:
                v_mult = 1.05
                t_mult = 1.02
                p_drop = 0.1
                hours_pm = 450
                
            input_dict = {
                "vibration_rms_mm_s": round(machine["nominal_vib_rms"] * v_mult, 2),
                "vibration_peak_accel_g": round(machine["nominal_vib_rms"] * v_mult * 2.2, 2),
                "bearing_temp_celsius": round(machine["nominal_temp"] * t_mult, 1),
                "motor_casing_temp_celsius": round(machine["nominal_temp"] * t_mult + 5.0, 1),
                "lube_oil_pressure_bar": round(max(machine["nominal_pressure"] - p_drop, 2.0), 2),
                "oil_particle_count_ppm": 350 if health == "Critical" else (160 if health == "Warning" else 30),
                "acoustic_emission_db": 84.0 if health == "Critical" else (68.0 if health == "Warning" else 48.0),
                "electrical_current_load_pct": round(machine["nominal_load"] * (1.25 if health == "Critical" else 1.05), 1),
                "rotational_speed_rpm": int(machine["nominal_rpm"]),
                "tool_wear_index_pct": 85.0 if health == "Critical" else (55.0 if health == "Warning" else 25.0),
                "operating_hours_since_pm": hours_pm,
                "cumulative_lifetime_hours": int(machine["cumulative_lifetime_hours"]),
                "historical_mtbf_hours": int(machine["historical_mtbf_hours"]),
                "historical_mttr_hours": float(machine["historical_mttr_hours"]),
                "past_failure_count": 3 if health == "Critical" else 1,
                "technician_qualification_level": 3,
                "component_health_score": 25.0 if health == "Critical" else (65.0 if health == "Warning" else 92.0),
                "hours_to_next_maintenance_window": 18.0 if health == "Critical" else 36.0,
                "scheduled_shift_units": 450
            }
            
            pred = analyzer.predict_single(input_dict)
            op_context = {
                "hours_to_next_maintenance_window": input_dict["hours_to_next_maintenance_window"],
                "batch_priority_tier": "Tier 1 (Urgent/Penalized)" if health == "Critical" else "Tier 2 (Standard Contract)",
                "downtime_cost_per_hour_usd": machine["downtime_cost_per_hour_usd"]
            }
            proto = self.formulate_recommendation(pred, op_context)
            
            results.append({
                "machine_id": machine["machine_id"],
                "machine_name": machine["machine_name"],
                "asset_model": machine["asset_model"],
                "plant_name": machine["plant_name"],
                "location": machine["location"],
                "health_status": health,
                "downtime_cost_hr": machine["downtime_cost_per_hour_usd"],
                "prediction": pred,
                "protocol": proto,
                "current_sensors": {
                    "vibration_rms": input_dict["vibration_rms_mm_s"],
                    "bearing_temp": input_dict["bearing_temp_celsius"],
                    "lube_pressure": input_dict["lube_oil_pressure_bar"],
                    "acoustic_db": input_dict["acoustic_emission_db"],
                    "electrical_load": input_dict["electrical_current_load_pct"]
                }
            })
            
        return results

if __name__ == "__main__":
    print("[PrescriptiveEngine] Module compiled successfully.")

