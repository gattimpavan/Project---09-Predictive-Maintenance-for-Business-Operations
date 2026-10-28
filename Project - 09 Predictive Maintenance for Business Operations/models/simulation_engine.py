"""
Siemens AG - What-If Counterfactual Simulation Engine
Project - 09: Predictive Maintenance for Business Operations

Simulates machine degradation under varied operating loads, coolant interventions,
and proactive operational throttling:
- Before vs After Intervention Comparison
- Sensor Threshold Stress-Testing
- Dynamic Extension of Remaining Useful Life (RUL)
- Net Risk Mitigation and Financial Exposure Reduction
"""

import os
import copy
import numpy as np

class SimulationEngine:
    def __init__(self, analyzer, prescriptive_engine):
        self.analyzer = analyzer
        self.prescriptive_engine = prescriptive_engine

    def run_counterfactual_simulation(self, baseline_params, interventions=None):
        """
        Takes baseline sensor telemetry, applies simulated physical interventions,
        and computes before-and-after diagnostics, RUL gain, and economic exposure reduction.
        """
        interventions = interventions or {}
        
        # 1. Evaluate baseline state
        base_pred = self.analyzer.predict_single(baseline_params)
        base_context = {
            "hours_to_next_maintenance_window": baseline_params.get("hours_to_next_maintenance_window", 24.0),
            "batch_priority_tier": baseline_params.get("batch_priority_tier", "Tier 2 (Standard Contract)"),
            "downtime_cost_per_hour_usd": baseline_params.get("downtime_cost_per_hour_usd", 280000)
        }
        base_proto = self.prescriptive_engine.formulate_recommendation(base_pred, base_context)
        
        # 2. Synthesize modified operating state after interventions
        modified_params = copy.deepcopy(baseline_params)
        
        # Interventions can include:
        # - load_throttle_pct: e.g. -18% (reduces speed, load, temp, vibe)
        # - coolant_flush: e.g. True (reduces bearing temp by 15°C, motor temp by 10°C)
        # - lube_replenish: e.g. True (restores pressure to 5.2 bar, drops acoustic dB by 18 dB)
        # - direct slider overrides
        
        throttle_pct = float(interventions.get("load_throttle_pct", 0.0))
        coolant_boost = bool(interventions.get("coolant_flush", False))
        lube_replenish = bool(interventions.get("lube_replenish", False))
        
        # Apply throttle physics
        if throttle_pct > 0:
            factor = (100.0 - throttle_pct) / 100.0
            modified_params["electrical_current_load_pct"] = round(modified_params["electrical_current_load_pct"] * factor, 1)
            modified_params["rotational_speed_rpm"] = int(modified_params["rotational_speed_rpm"] * (0.95 + 0.05 * factor))
            modified_params["vibration_rms_mm_s"] = round(max(modified_params["vibration_rms_mm_s"] * (0.70 + 0.30 * factor), 1.2), 2)
            modified_params["vibration_peak_accel_g"] = round(modified_params["vibration_rms_mm_s"] * 1.8, 2)
            modified_params["bearing_temp_celsius"] = round(max(modified_params["bearing_temp_celsius"] * (0.85 + 0.15 * factor), 45.0), 1)
            
        if coolant_boost:
            modified_params["bearing_temp_celsius"] = round(max(modified_params["bearing_temp_celsius"] - 14.5, 42.0), 1)
            modified_params["motor_casing_temp_celsius"] = round(max(modified_params["motor_casing_temp_celsius"] - 11.0, 48.0), 1)
            
        if lube_replenish:
            modified_params["lube_oil_pressure_bar"] = round(max(modified_params["lube_oil_pressure_bar"] + 1.6, 5.2), 2)
            modified_params["oil_particle_count_ppm"] = int(modified_params["oil_particle_count_ppm"] * 0.35)
            modified_params["acoustic_emission_db"] = round(max(modified_params["acoustic_emission_db"] - 16.0, 44.0), 1)
            
        # Also support manual direct overrides from dashboard sliders
        for k in ["vibration_rms_mm_s", "bearing_temp_celsius", "lube_oil_pressure_bar", 
                  "acoustic_emission_db", "electrical_current_load_pct", "rotational_speed_rpm"]:
            if k in interventions:
                modified_params[k] = float(interventions[k])
                
        # Re-evaluate modified state
        mod_pred = self.analyzer.predict_single(modified_params)
        mod_proto = self.prescriptive_engine.formulate_recommendation(mod_pred, base_context)
        
        # Calculate Delta Improvements
        rul_gain_hrs = round(mod_pred["predicted_rul_hours"] - base_pred["predicted_rul_hours"], 1)
        risk_reduction_pct = round(base_pred["failure_risk_pct"] - mod_pred["failure_risk_pct"], 1)
        hourly_cost = base_context["downtime_cost_per_hour_usd"]
        
        # Financial exposure calculation
        baseline_financial_exposure = round((base_pred["failure_probability"] * hourly_cost * 6.5), 2)
        mitigated_financial_exposure = round((mod_pred["failure_probability"] * hourly_cost * 6.5), 2)
        financial_risk_avoidance = round(baseline_financial_exposure - mitigated_financial_exposure, 2)
        
        return {
            "baseline": {
                "parameters": baseline_params,
                "prediction": base_pred,
                "protocol": base_proto,
                "financial_exposure_usd": baseline_financial_exposure
            },
            "mitigated": {
                "parameters": modified_params,
                "prediction": mod_pred,
                "protocol": mod_proto,
                "financial_exposure_usd": mitigated_financial_exposure
            },
            "delta": {
                "rul_gain_hours": rul_gain_hrs,
                "risk_reduction_percentage": risk_reduction_pct,
                "financial_risk_avoidance_usd": financial_risk_avoidance,
                "intervention_effectiveness": "Optimal Stabilization" if risk_reduction_pct > 35 else ("Moderate Mitigation" if risk_reduction_pct > 15 else "Marginal Shift")
            }
        }

if __name__ == "__main__":
    print("[SimulationEngine] Module compiled successfully.")

