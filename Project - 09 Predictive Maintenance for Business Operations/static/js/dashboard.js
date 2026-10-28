/**
 * Siemens AG - Predictive Maintenance Platform
 * Frontend Interactive Dashboard Controller
 */

let allMachines = [];
let currentSelectedMachineId = null;
let simulationDebounceTimer = null;

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initFilterEvents();
    initSimulationControls();
    loadFleetSummary();
    loadMachines();
});

// ================= Tab Management =================
function initTabs() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

            tab.classList.add("active");
            const targetPane = document.getElementById(tab.dataset.tab);
            if (targetPane) {
                targetPane.classList.add("active");
            }
        });
    });
}

// ================= Global Fleet Summary =================
async function loadFleetSummary() {
    try {
        const res = await fetch("/api/fleet_summary");
        const data = await res.json();
        if (data.status === "success") {
            document.getElementById("kpiFleetCount").innerText = `${data.total_machines} Assets`;
            document.getElementById("kpiFleetHealth").innerText = `${data.health_distribution.fleet_health_score_pct}%`;
            document.getElementById("kpiHealthBreakdown").innerText = 
                `${data.health_distribution.optimal} Optimal | ${data.health_distribution.warning} Warn | ${data.health_distribution.critical} Crit`;
            document.getElementById("kpiWarningHorizon").innerText = `${data.early_warning_horizon_hours} Hours`;
            document.getElementById("kpiDowntimeSaved").innerText = `${data.total_downtime_hours_prevented.toLocaleString()} Hours`;
            document.getElementById("kpiPreservedValue").innerText = `$${data.total_preserved_value_millions}M USD`;
        }
    } catch (err) {
        console.error("Error loading fleet summary:", err);
    }
}

// ================= Fleet Machines Ingestion =================
async function loadMachines() {
    try {
        const res = await fetch("/api/machines");
        const data = await res.json();
        if (data.status === "success") {
            allMachines = data.machines;
            renderFleetGrid(allMachines);
            renderMachineSelector(allMachines);
            renderSchedulerTable(allMachines);

            // Select first machine by default
            if (allMachines.length > 0) {
                selectMachine(allMachines[0].machine_id);
            }
        }
    } catch (err) {
        console.error("Error loading fleet machines:", err);
    }
}

// ================= Filters & Search =================
function initFilterEvents() {
    const plantSelect = document.getElementById("filterPlant");
    const typeSelect = document.getElementById("filterAssetType");
    const statusSelect = document.getElementById("filterHealthStatus");
    const searchInput = document.getElementById("fleetSearchInput");

    const applyFilters = () => {
        const plant = plantSelect.value;
        const type = typeSelect.value;
        const status = statusSelect.value;
        const query = searchInput.value.toLowerCase().trim();

        const filtered = allMachines.filter(m => {
            const matchesPlant = (plant === "ALL" || m.plant_name.includes(plant));
            const matchesType = (type === "ALL" || m.asset_model.includes(type));
            const matchesStatus = (status === "ALL" || m.health_status === status);
            const matchesQuery = (!query || 
                m.machine_id.toLowerCase().includes(query) ||
                m.machine_name.toLowerCase().includes(query) ||
                m.plant_name.toLowerCase().includes(query) ||
                m.asset_model.toLowerCase().includes(query)
            );
            return matchesPlant && matchesType && matchesStatus && matchesQuery;
        });

        renderFleetGrid(filtered);
    };

    plantSelect.addEventListener("change", applyFilters);
    typeSelect.addEventListener("change", applyFilters);
    statusSelect.addEventListener("change", applyFilters);
    searchInput.addEventListener("input", applyFilters);
}

// ================= Render Fleet Grid Cards =================
function renderFleetGrid(machines) {
    const container = document.getElementById("fleetGridContainer");
    if (!machines || machines.length === 0) {
        container.innerHTML = `<div class="empty-msg"><i class="fa-solid fa-filter"></i> No Siemens machine assets match current filters.</div>`;
        return;
    }

    container.innerHTML = machines.map(m => {
        const statusClass = m.health_status.toLowerCase();
        const pred = m.prediction;
        const proto = m.protocol;
        const sensors = m.current_sensors;
        const rulPct = Math.min((pred.predicted_rul_hours / 350.0) * 100, 100);

        let rulBarColor = "#00E5FF";
        if (pred.predicted_rul_hours < 24) rulBarColor = "#FF3366";
        else if (pred.predicted_rul_hours < 72) rulBarColor = "#FFB300";

        return `
            <div class="machine-card status-${statusClass}" onclick="openMachineDeepDive('${m.machine_id}')">
                <div class="card-top">
                    <div class="card-title-wrap">
                        <span class="card-id-tag">${m.machine_id}</span>
                        <h4>${m.machine_name}</h4>
                    </div>
                    <span class="status-badge ${statusClass}">${m.health_status}</span>
                </div>

                <div class="card-meta-text">
                    <i class="fa-solid fa-location-dot"></i> ${m.plant_name.replace("Siemens ", "")}
                </div>

                <div class="card-telemetry-row">
                    <div class="telemetry-item">
                        <span class="lbl">Vibe RMS</span>
                        <span class="val">${sensors.vibration_rms} <small>mm/s</small></span>
                    </div>
                    <div class="telemetry-item">
                        <span class="lbl">Brg Temp</span>
                        <span class="val">${sensors.bearing_temp} <small>°C</small></span>
                    </div>
                    <div class="telemetry-item">
                        <span class="lbl">Pressure</span>
                        <span class="val">${sensors.lube_pressure} <small>bar</small></span>
                    </div>
                </div>

                <div class="card-rul-bar">
                    <div class="rul-header">
                        <span>RUL Countdown: <b>${pred.predicted_rul_hours}h</b></span>
                        <span>Risk: <b>${pred.failure_risk_pct}%</b></span>
                    </div>
                    <div class="rul-track">
                        <div class="rul-fill" style="width: ${rulPct}%; background: ${rulBarColor};"></div>
                    </div>
                </div>

                <div class="card-protocol-strip">
                    <span class="proto-label-tag" style="color: ${proto.badge_color};">
                        <i class="fa-solid fa-shield"></i> ${proto.protocol_code}
                    </span>
                    <span style="color: var(--accent-emerald); font-weight: 600;">
                        Preserved: $${(proto.net_preserved_value_usd / 1000).toFixed(0)}k
                    </span>
                </div>
            </div>
        `;
    }).join("");
}

// ================= Machine Deep-Dive Navigation =================
function openMachineDeepDive(machineId) {
    // Switch tab
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

    const deepDiveTab = document.querySelector('[data-tab="tab-deepdive"]');
    deepDiveTab.classList.add("active");
    document.getElementById("tab-deepdive").classList.add("active");

    selectMachine(machineId);
}

function renderMachineSelector(machines) {
    const list = document.getElementById("deepdiveMachineList");
    list.innerHTML = machines.map(m => `
        <div class="machine-item-pill ${m.machine_id === currentSelectedMachineId ? 'active' : ''}" 
             id="pill-${m.machine_id}" 
             onclick="selectMachine('${m.machine_id}')">
            <div class="pill-top">
                <span class="pill-id">${m.machine_id}</span>
                <span class="status-badge ${m.health_status.toLowerCase()}">${m.health_status}</span>
            </div>
            <span class="pill-name">${m.machine_name}</span>
        </div>
    `).join("");
}

function selectMachine(machineId) {
    currentSelectedMachineId = machineId;

    // Update active class in selector
    document.querySelectorAll(".machine-item-pill").forEach(p => p.classList.remove("active"));
    const activePill = document.getElementById(`pill-${machineId}`);
    if (activePill) activePill.classList.add("active");

    const machine = allMachines.find(m => m.machine_id === machineId);
    if (!machine) return;

    // Update Detail Header
    document.getElementById("detailMachineTag").innerText = machine.machine_id;
    document.getElementById("detailMachineName").innerText = machine.machine_name;
    document.getElementById("detailMachineMeta").innerHTML = 
        `<i class="fa-solid fa-location-dot"></i> ${machine.plant_name} | ${machine.location} | Downtime Cost: $${machine.downtime_cost_hr.toLocaleString()}/hr`;
    
    const badge = document.getElementById("detailStatusBadge");
    badge.className = `status-badge ${machine.health_status.toLowerCase()}`;
    badge.innerText = machine.health_status;

    // Update Sensors
    const s = machine.current_sensors;
    document.getElementById("gaugeVibration").innerHTML = `${s.vibration_rms} <span class="unit">mm/s</span>`;
    document.getElementById("gaugeBarVib").style.width = `${Math.min((s.vibration_rms / 8.0) * 100, 100)}%`;

    document.getElementById("gaugeTemp").innerHTML = `${s.bearing_temp} <span class="unit">°C</span>`;
    document.getElementById("gaugeBarTemp").style.width = `${Math.min((s.bearing_temp / 100.0) * 100, 100)}%`;

    document.getElementById("gaugePressure").innerHTML = `${s.lube_pressure} <span class="unit">bar</span>`;
    document.getElementById("gaugeBarPress").style.width = `${Math.min((s.lube_pressure / 6.5) * 100, 100)}%`;

    document.getElementById("gaugeAcoustic").innerHTML = `${s.acoustic_db} <span class="unit">dB</span>`;
    document.getElementById("gaugeBarAcoustic").style.width = `${Math.min((s.acoustic_db / 95.0) * 100, 100)}%`;

    document.getElementById("gaugeLoad").innerHTML = `${s.electrical_load} <span class="unit">%</span>`;
    document.getElementById("gaugeBarLoad").style.width = `${Math.min((s.electrical_load / 130.0) * 100, 100)}%`;

    // Update Diagnostics
    const pred = machine.prediction;
    document.getElementById("diagFailureProb").innerText = `${pred.failure_risk_pct}%`;
    document.getElementById("diagPattern").innerText = pred.diagnosed_pattern;
    document.getElementById("diagRUL").innerText = `${pred.predicted_rul_hours} Hours`;

    const anomBadge = document.getElementById("diagAnomalyBadge");
    if (pred.is_anomaly) {
        anomBadge.innerText = "Anomaly Detected";
        anomBadge.style.color = "#FF3366";
        anomBadge.style.borderColor = "rgba(255, 51, 102, 0.4)";
    } else {
        anomBadge.innerText = "Normal Telemetry Signature";
        anomBadge.style.color = "#00E676";
        anomBadge.style.borderColor = "rgba(0, 230, 118, 0.4)";
    }

    // Pattern probabilities
    const probsContainer = document.getElementById("patternProbsList");
    probsContainer.innerHTML = Object.entries(pred.pattern_probabilities).map(([cls, prob]) => {
        const pct = (prob * 100).toFixed(1);
        return `
            <div class="pattern-prob-row">
                <span class="pattern-lbl">${cls.replace("_", " ")}</span>
                <div class="pattern-bar-track">
                    <div class="pattern-bar-fill" style="width: ${pct}%;"></div>
                </div>
                <span class="pattern-pct">${pct}%</span>
            </div>
        `;
    }).join("");

    // Update Protocol
    const proto = machine.protocol;
    const protoBadge = document.getElementById("protoBadge");
    protoBadge.innerText = proto.protocol_code;
    protoBadge.style.color = proto.badge_color;
    protoBadge.style.borderColor = proto.badge_color;

    document.getElementById("protoName").innerText = proto.protocol_name;
    document.getElementById("protoSummary").innerText = proto.action_summary;
    document.getElementById("protoTech").innerText = proto.required_tech_grade;
    document.getElementById("protoBOM").innerText = proto.spare_parts_kit;
    document.getElementById("protoMTTR").innerText = `${proto.expected_mttr_hrs} Hours`;
    document.getElementById("protoSavedHours").innerText = `${proto.prevented_downtime_hrs} Hours Saved`;
    document.getElementById("protoPreservedValue").innerText = `$${proto.net_preserved_value_usd.toLocaleString()}`;

    // Steps
    const stepsList = document.getElementById("protoStepsList");
    stepsList.innerHTML = proto.operational_steps.map(step => `<li>${step}</li>`).join("");

    // Dispatch button
    const btnDispatch = document.getElementById("btnDispatchWorkOrder");
    btnDispatch.onclick = () => dispatchWorkOrder(machine.machine_id, proto.protocol_code);
}

// ================= Work Order Dispatch =================
async function dispatchWorkOrder(machineId, protocolCode) {
    try {
        const res = await fetch("/api/dispatch_protocol", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ machine_id: machineId, protocol_code: protocolCode })
        });
        const data = await res.json();
        if (data.status === "success") {
            showToast("Work Order Dispatched", `Order ${data.confirmation_code} dispatched to Siemens MindSphere for ${machineId}.`);
        }
    } catch (err) {
        showToast("Dispatch Failed", "Could not reach MindSphere Gateway.", true);
    }
}

// ================= MES Scheduler Table =================
function renderSchedulerTable(machines) {
    const tbody = document.getElementById("schedulerTableBody");
    const shifts = ["Shift A (Morning)", "Shift B (Evening)", "Shift C (Night)"];
    const tiers = ["Tier 1 (Urgent/Penalized)", "Tier 2 (Standard Contract)", "Tier 3 (Buffer Shift)"];

    tbody.innerHTML = machines.slice(0, 15).map((m, idx) => {
        const shift = shifts[idx % 3];
        const tier = tiers[idx % 3];
        const pred = m.prediction;
        const rul = pred.predicted_rul_hours;
        const windowHrs = 18.0 + (idx * 3.5);
        const delta = (rul - windowHrs).toFixed(1);
        const deltaColor = delta < 0 ? '#FF3366' : '#00E676';

        let tierClass = "tier2";
        if (tier.includes("Tier 1")) tierClass = "tier1";
        else if (tier.includes("Tier 3")) tierClass = "tier3";

        return `
            <tr>
                <td><b>${m.machine_id}</b><br/><small>${m.asset_model.split(" ")[0]} ${m.asset_model.split(" ")[1] || ""}</small></td>
                <td><span style="font-family: var(--font-mono);">JOB-SMN-${92000 + idx}</span></td>
                <td><span class="legend-pill ${tierClass}">${tier.split(" ")[0]} ${tier.split(" ")[1]}</span></td>
                <td>${shift}</td>
                <td><b>${windowHrs.toFixed(1)} Hours</b></td>
                <td><b style="color: ${pred.failure_risk_pct > 50 ? '#FF3366' : '#00E676'};">${pred.failure_risk_pct}%</b></td>
                <td><b style="color: ${deltaColor};">${delta > 0 ? '+' : ''}${delta}h</b></td>
                <td>
                    <button class="btn btn-primary" style="padding: 4px 10px; font-size: 0.72rem;" onclick="openMachineDeepDive('${m.machine_id}')">
                        <i class="fa-solid fa-wrench"></i> ${m.protocol.protocol_code.replace("PROTOCOL_", "")}
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

// ================= What-If Counterfactual Simulator =================
function initSimulationControls() {
    const sliders = [
        { id: "sliderVibRms", labelId: "valVibRms", unit: " mm/s", key: "vibration_rms_mm_s" },
        { id: "sliderBearingTemp", labelId: "valBearingTemp", unit: " °C", key: "bearing_temp_celsius" },
        { id: "sliderLubePress", labelId: "valLubePress", unit: " bar", key: "lube_oil_pressure_bar" },
        { id: "sliderAcousticDb", labelId: "valAcousticDb", unit: " dB", key: "acoustic_emission_db" },
        { id: "sliderElecLoad", labelId: "valElecLoad", unit: " %", key: "electrical_current_load_pct" },
        { id: "sliderRpm", labelId: "valRpm", unit: " RPM", key: "rotational_speed_rpm" }
    ];

    sliders.forEach(s => {
        const sliderEl = document.getElementById(s.id);
        const labelEl = document.getElementById(s.labelId);
        sliderEl.addEventListener("input", () => {
            labelEl.innerText = `${sliderEl.value}${s.unit}`;
            debounceRunSimulation();
        });
    });

    // Checkboxes
    document.getElementById("chkThrottle").addEventListener("change", debounceRunSimulation);
    document.getElementById("chkCoolant").addEventListener("change", debounceRunSimulation);
    document.getElementById("chkLube").addEventListener("change", debounceRunSimulation);

    // Presets
    const presets = {
        nominal: { vib: 1.4, temp: 52.0, press: 5.2, acoustic: 46.0, load: 72, rpm: 6000 },
        bearing: { vib: 6.8, temp: 78.5, press: 4.8, acoustic: 82.0, load: 88, rpm: 5800 },
        thermal: { vib: 3.5, temp: 96.0, press: 4.2, acoustic: 72.0, load: 110, rpm: 5600 },
        lubrication: { vib: 4.2, temp: 84.0, press: 2.1, acoustic: 78.0, load: 85, rpm: 5900 },
        tooling: { vib: 4.8, temp: 66.0, press: 5.0, acoustic: 88.5, load: 94, rpm: 5750 }
    };

    document.querySelectorAll(".preset-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".preset-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const p = presets[btn.dataset.preset];
            if (p) {
                document.getElementById("sliderVibRms").value = p.vib;
                document.getElementById("valVibRms").innerText = `${p.vib} mm/s`;

                document.getElementById("sliderBearingTemp").value = p.temp;
                document.getElementById("valBearingTemp").innerText = `${p.temp} °C`;

                document.getElementById("sliderLubePress").value = p.press;
                document.getElementById("valLubePress").innerText = `${p.press} bar`;

                document.getElementById("sliderAcousticDb").value = p.acoustic;
                document.getElementById("valAcousticDb").innerText = `${p.acoustic} dB`;

                document.getElementById("sliderElecLoad").value = p.load;
                document.getElementById("valElecLoad").innerText = `${p.load} %`;

                document.getElementById("sliderRpm").value = p.rpm;
                document.getElementById("valRpm").innerText = `${p.rpm} RPM`;

                debounceRunSimulation();
            }
        });
    });

    // Run initial simulation
    runSimulation();
}

function debounceRunSimulation() {
    clearTimeout(simulationDebounceTimer);
    simulationDebounceTimer = setTimeout(runSimulation, 250);
}

async function runSimulation() {
    const baseParams = {
        vibration_rms_mm_s: parseFloat(document.getElementById("sliderVibRms").value),
        bearing_temp_celsius: parseFloat(document.getElementById("sliderBearingTemp").value),
        lube_oil_pressure_bar: parseFloat(document.getElementById("sliderLubePress").value),
        acoustic_emission_db: parseFloat(document.getElementById("sliderAcousticDb").value),
        electrical_current_load_pct: parseFloat(document.getElementById("sliderElecLoad").value),
        rotational_speed_rpm: parseInt(document.getElementById("sliderRpm").value),
        downtime_cost_per_hour_usd: 310000,
        batch_priority_tier: "Tier 1 (Urgent/Penalized)"
    };

    const interventions = {
        load_throttle_pct: document.getElementById("chkThrottle").checked ? 18.0 : 0.0,
        coolant_flush: document.getElementById("chkCoolant").checked,
        lube_replenish: document.getElementById("chkLube").checked
    };

    try {
        const res = await fetch("/api/simulate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ baseline: baseParams, interventions: interventions })
        });
        const data = await res.json();
        if (data.status === "success") {
            const sim = data.simulation;
            const delta = sim.delta;
            const b = sim.baseline;
            const m = sim.mitigated;

            // Delta Cards
            document.getElementById("simRulGain").innerText = `${delta.rul_gain_hours > 0 ? '+' : ''}${delta.rul_gain_hours} Hours`;
            document.getElementById("simRulSub").innerText = `Baseline: ${b.prediction.predicted_rul_hours}h → Mitigated: ${m.prediction.predicted_rul_hours}h`;

            document.getElementById("simRiskReduction").innerText = `-${delta.risk_reduction_percentage}%`;
            document.getElementById("simRiskSub").innerText = `Baseline: ${b.prediction.failure_risk_pct}% → Mitigated: ${m.prediction.failure_risk_pct}%`;

            document.getElementById("simRiskAvoidance").innerText = `$${delta.financial_risk_avoidance_usd.toLocaleString()}`;
            document.getElementById("simEffectivenessBadge").innerText = delta.intervention_effectiveness;

            // Table Rows
            document.getElementById("rowBaseProb").innerText = `${b.prediction.failure_risk_pct}%`;
            document.getElementById("rowMitProb").innerText = `${m.prediction.failure_risk_pct}%`;

            document.getElementById("rowBasePattern").innerText = b.prediction.diagnosed_pattern;
            document.getElementById("rowMitPattern").innerText = m.prediction.diagnosed_pattern;

            document.getElementById("rowBaseRUL").innerText = `${b.prediction.predicted_rul_hours}h`;
            document.getElementById("rowMitRUL").innerText = `${m.prediction.predicted_rul_hours}h`;

            document.getElementById("rowBaseProto").innerText = b.protocol.protocol_code;
            document.getElementById("rowMitProto").innerText = m.protocol.protocol_code;

            document.getElementById("rowBaseExp").innerText = `$${b.financial_exposure_usd.toLocaleString()}`;
            document.getElementById("rowMitExp").innerText = `$${m.financial_exposure_usd.toLocaleString()}`;
        }
    } catch (err) {
        console.error("Simulation error:", err);
    }
}

// ================= Toast Notifications =================
function showToast(title, message, isError = false) {
    const toast = document.getElementById("globalToast");
    const tTitle = document.getElementById("toastTitle");
    const tMsg = document.getElementById("toastMessage");

    tTitle.innerText = title;
    tMsg.innerText = message;

    if (isError) {
        toast.style.borderColor = "var(--accent-crimson)";
        toast.querySelector("i").className = "fa-solid fa-triangle-exclamation";
        toast.querySelector("i").style.color = "var(--accent-crimson)";
    } else {
        toast.style.borderColor = "var(--siemens-teal)";
        toast.querySelector("i").className = "fa-solid fa-circle-check";
        toast.querySelector("i").style.color = "var(--siemens-teal)";
    }

    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 4500);
}

