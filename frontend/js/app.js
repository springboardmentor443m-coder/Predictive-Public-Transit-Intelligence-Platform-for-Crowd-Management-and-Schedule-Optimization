/* =========================================================
   V/LINE PUBLIC TRANSPORT INTELLIGENCE
   Main frontend application
   ========================================================= */

"use strict";

/* ========================= CONFIGURATION ========================= */

const API_BASE = "http://127.0.0.1:5000";

const API_ENDPOINTS = {
    health: "/api/health",
    summary: "/api/summary",
    routes: "/api/routes",
    stops: "/api/stops",
    crowd: "/api/crowd?hour=17",
    optimization: "/api/optimization",
    priorityStations: "/api/priority-stops",
    delayModel: "/api/delay-model"
};


/* ========================= GENERAL HELPERS ========================= */

async function fetchAPI(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "GET",
        headers: {
            Accept: "application/json"
        }
    });

    if (!response.ok) {
        throw new Error(
            `API request failed: ${response.status} ${response.statusText}`
        );
    }

    return response.json();
}


function escapeHTML(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function getValue(object, keys, fallback = "N/A") {
    if (!object || typeof object !== "object") {
        return fallback;
    }

    for (const key of keys) {
        if (
            object[key] !== undefined &&
            object[key] !== null &&
            object[key] !== ""
        ) {
            return object[key];
        }
    }

    return fallback;
}


function asArray(data) {
    if (Array.isArray(data)) {
        return data;
    }

    if (!data || typeof data !== "object") {
        return [];
    }

    const possibleKeys = [
        "data",
        "results",
        "records",
        "items",
        "crowd",
        "features",
        "recommendations",
        "priority_stops",
        "stops",
        "routes"
    ];

    for (const key of possibleKeys) {
        if (Array.isArray(data[key])) {
            return data[key];
        }
    }

    return [];
}


function normalizeCategory(value) {
    return String(value ?? "")
        .trim()
        .toUpperCase()
        .replace(/[\s-]+/g, "_");
}


function number(value, decimals = 0) {
    const parsed = Number(value);

    if (!Number.isFinite(parsed)) {
        return "N/A";
    }

    return parsed.toLocaleString("en-US", {
        maximumFractionDigits: decimals,
        minimumFractionDigits: decimals
    });
}


function formatPressure(value) {
    const parsed = Number(value);

    if (!Number.isFinite(parsed)) {
        return "N/A";
    }

    // Scores in this dataset are represented between 0 and 1.
    const percentage = parsed <= 1 ? parsed * 100 : parsed;

    return `${number(percentage, 1)}%`;
}


function formatDelay(seconds) {
    const parsed = Number(seconds);

    if (!Number.isFinite(parsed)) {
        return "N/A";
    }

    const sign = parsed < 0 ? "-" : "";
    const absolute = Math.abs(Math.round(parsed));
    const minutes = Math.floor(absolute / 60);
    const remainingSeconds = absolute % 60;

    return `${sign}${minutes} min ${remainingSeconds} sec`;
}


function getStopName(item) {
    return getValue(item, [
        "stop_name",
        "station_name",
        "stop",
        "name"
    ]);
}


function getRouteName(item) {
    return getValue(item, [
        "route_name",
        "route_short_name",
        "route_id",
        "route"
    ]);
}


function getCategoryClass(value) {
    const category = normalizeCategory(value);

    if (
        category.includes("HIGH") ||
        category.includes("PRIORITY") ||
        category.includes("ADDITIONAL_SERVICE")
    ) {
        return "danger";
    }

    if (
        category.includes("MEDIUM") ||
        category.includes("MONITOR") ||
        category.includes("WAITING")
    ) {
        return "waiting";
    }

    if (
        category.includes("LOW") ||
        category.includes("NORMAL") ||
        category.includes("NO_CHANGE") ||
        category.includes("HEALTHY") ||
        category.includes("READY")
    ) {
        return "success";
    }

    return "neutral";
}


function makePill(label, style = "neutral") {
    return `
        <span class="pill ${escapeHTML(style)}">
            ${escapeHTML(label)}
        </span>
    `;
}


function setText(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.textContent = value ?? "";
    }
}


function renderEmpty(message) {
    return `
        <div class="empty-state">
            ${escapeHTML(message)}
        </div>
    `;
}


function showLoading(container, message = "Loading data...") {
    if (!container) return;

    container.innerHTML = `
        <div class="loading-state">
            ${escapeHTML(message)}
        </div>
    `;
}


function showError(container, message) {
    if (!container) return;

    container.innerHTML = `
        <div class="error-state">
            ${escapeHTML(message)}
        </div>
    `;
}


function renderDataRow(label, value) {
    return `
        <div class="data-row">
            <span>${escapeHTML(label)}</span>
            <strong>${escapeHTML(value)}</strong>
        </div>
    `;
}


function renderDataCard(title, rows, category = null) {
    return `
        <article class="data-card">
            <h4>${escapeHTML(title)}</h4>

            ${
                category
                    ? makePill(
                        category,
                        getCategoryClass(category)
                    )
                    : ""
            }

            ${rows.join("")}
        </article>
    `;
}


/* ========================= NAVIGATION ========================= */

function initializeNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const sections = document.querySelectorAll(".dashboard-section");

    if (!navItems.length || !sections.length) {
        return;
    }

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const target = item.dataset.section;

            if (!target) return;

            navItems.forEach(nav => {
                nav.classList.remove("active");
            });

            item.classList.add("active");

            sections.forEach(section => {
                section.classList.toggle(
                    "active",
                    section.id === target
                );
            });
        });
    });
}


/* ========================= BACKEND HEALTH ========================= */

async function loadHealth() {
    try {
        const data = await fetchAPI(API_ENDPOINTS.health);

        const healthy =
            data.status === "healthy" ||
            data.status === "ok" ||
            data.healthy === true;

        const statusText = healthy
            ? "Backend Connected"
            : "Backend Status: " + String(data.status ?? "Unknown");

        const statusElement =
            document.getElementById("backend-status") ||
            document.querySelector(".backend-status");

        if (statusElement) {
            statusElement.textContent = statusText;
            statusElement.classList.toggle("success", healthy);
            statusElement.classList.toggle("danger", !healthy);
        }

        setText("connection-status", statusText);

    } catch (error) {
        console.error("Backend health check failed:", error);

        const statusElement =
            document.getElementById("backend-status") ||
            document.querySelector(".backend-status");

        if (statusElement) {
            statusElement.textContent = "Backend Disconnected";
            statusElement.classList.add("danger");
        }

        setText("connection-status", "Backend Disconnected");
    }
}


/* ========================= OVERVIEW SUMMARY ========================= */

async function loadSummary() {
    try {
        const data = await fetchAPI(API_ENDPOINTS.summary);

        // These IDs match the metric elements in frontend/index.html.
        const metrics = {
            "metric-routes": [
                "routes",
                "total_routes",
                "route_count"
            ],
            "metric-stops": [
                "stops",
                "total_stops",
                "stop_count"
            ],
            "metric-trips": [
                "trips",
                "total_trips",
                "trip_count"
            ],
            "metric-features": [
                "feature_observations",
                "total_feature_observations",
                "observation_count"
            ]
        };

        Object.entries(metrics).forEach(([id, keys]) => {
            const element = document.getElementById(id);

            if (!element) {
                console.warn(`Summary metric element #${id} was not found.`);
                return;
            }

            const value = getValue(data, keys, null);

            if (value !== null) {
                element.textContent = number(value);
            } else {
                console.warn(`Summary API did not return a value for #${id}.`);
            }
        });

        // Support any additional summary fields explicitly mapped in HTML.
        document.querySelectorAll("[data-summary-key]").forEach(element => {
            const key = element.dataset.summaryKey;

            if (
                key &&
                data[key] !== undefined &&
                data[key] !== null
            ) {
                element.textContent = number(data[key]);
            }
        });
    } catch (error) {
        console.error("Summary loading failed:", error);
    }
}

/* ========================= CROWD MANAGEMENT ========================= */

async function loadCrowdData() {
    const container = document.getElementById("crowd-content");

    if (!container) {
        console.warn("Element #crowd-content was not found.");
        return;
    }

    showLoading(container, "Loading crowd management data...");

    try {
        const response = await fetchAPI(API_ENDPOINTS.crowd);
        const data = asArray(response);

        if (!data.length) {
            container.innerHTML = renderEmpty(
                "No crowd management records were returned by the API."
            );
            return;
        }

        const categories = [
            {
                value: "HIGH",
                label: "High Service Pressure",
                description:
                    "Stations classified as HIGH by the service-pressure calculation."
            },
            {
                value: "MEDIUM",
                label: "Medium Service Pressure",
                description:
                    "Stations classified as MEDIUM by the service-pressure calculation."
            },
            {
                value: "LOW",
                label: "Low Service Pressure",
                description:
                    "Stations classified as LOW by the service-pressure calculation."
            }
        ];

        container.innerHTML = categories.map(category => {
            const matching = data
                .filter(item =>
                    normalizeCategory(
                        item.service_pressure_category
                    ) === category.value
                )
                .sort((a, b) =>
                    Number(b.service_pressure_score ?? 0) -
                    Number(a.service_pressure_score ?? 0)
                );

            // Keep only the highest-pressure record per stop.
            const uniqueStops = new Map();

            matching.forEach(item => {
                const stopKey = String(
                    getValue(item, ["stop_id"], "")
                );

                if (!stopKey) return;

                if (!uniqueStops.has(stopKey)) {
                    uniqueStops.set(stopKey, item);
                }
            });

            const records = Array.from(uniqueStops.values()).slice(0, 3);

            const cards = records.map((item, index) => {
                const stopName = getStopName(item);
                const stopId = getValue(item, ["stop_id"]);
                const routeName = getRouteName(item);
                const hour = getValue(item, ["scheduled_hour"]);
                const peak = getValue(item, ["peak_period"]);
                const pressure = formatPressure(
                    item.service_pressure_score
                );
                const stopActivity = getValue(
                    item,
                    ["stop_activity_category"],
                    "UNKNOWN"
                );

                return `
                    <article class="data-card">
                        <h4>
                            ${index + 1}. ${escapeHTML(stopName)}
                        </h4>

                        ${makePill(
                            category.value,
                            getCategoryClass(category.value)
                        )}

                        ${renderDataRow("Stop ID", String(stopId))}
                        ${renderDataRow("Route", String(routeName))}
                        ${renderDataRow("Scheduled hour", String(hour))}
                        ${renderDataRow("Peak period", String(peak))}
                        ${renderDataRow("Service pressure", pressure)}

                        <div class="data-row">
                            <span>Stop activity</span>
                            ${makePill(
                                stopActivity,
                                getCategoryClass(stopActivity)
                            )}
                        </div>
                    </article>
                `;
            }).join("");

            return `
                <section class="data-group">
                    <h3>
                        ${escapeHTML(category.label)}
                        ${makePill(category.value, getCategoryClass(category.value))}
                    </h3>

                    <p class="section-description">
                        ${escapeHTML(category.description)}
                    </p>

                    <div class="data-grid">
                        ${
                            cards ||
                            renderEmpty(
                                `No records classified as ${category.value} ` +
                                "service pressure were returned by the API."
                            )
                        }
                    </div>
                </section>
            `;
        }).join("");

    } catch (error) {
        console.error("Crowd management loading failed:", error);

        showError(
            container,
            "Unable to load crowd management data. Check that the Flask backend is running on port 5000."
        );
    }
}


/* ========================= SCHEDULE OPTIMIZATION ========================= */

async function loadOptimizationData() {
    const container = document.getElementById("optimization-content");

    if (!container) {
        console.warn("Element #optimization-content was not found.");
        return;
    }

    showLoading(container, "Loading schedule optimization recommendations...");

    try {
        const response = await fetchAPI(API_ENDPOINTS.optimization);

        let records = asArray(response);

        // Some backend responses may separate schedule and stop recommendations.
        if (!records.length && response && typeof response === "object") {
            records = [
                ...asArray(response.schedule_recommendations),
                ...asArray(response.stop_recommendations),
                ...asArray(response.recommendations)
            ];
        }

        if (!records.length) {
            container.innerHTML = renderEmpty(
                "No schedule optimization recommendations are available."
            );
            return;
        }

        const cards = records.slice(0, 100).map((item, index) => {
            const route = getRouteName(item);
            const stop = getStopName(item);

            const recommendation = getValue(item, [
                "recommendation",
                "optimization_category",
                "recommendation_category",
                "category",
                "action"
            ], "MONITOR");

            const pressure = item.average_service_pressure ??
                item.service_pressure_score;

            const rows = [
                renderDataRow("Route", String(route)),
                renderDataRow("Stop", String(stop)),
                renderDataRow(
                    "Service pressure",
                    pressure !== undefined
                        ? formatPressure(pressure)
                        : "N/A"
                ),
                renderDataRow(
                    "Scheduled hour",
                    String(getValue(item, ["scheduled_hour"]))
                )
            ];

            return `
                <article class="data-card">
                    <h4>
                        ${index + 1}. ${escapeHTML(
                            getValue(item, [
                                "route_name",
                                "stop_name",
                                "route_id",
                                "stop_id"
                            ], "Service recommendation")
                        )}
                    </h4>

                    ${makePill(
                        recommendation,
                        getCategoryClass(recommendation)
                    )}

                    ${rows.join("")}

                    ${
                        item.reason || item.description
                            ? `<p>${escapeHTML(
                                item.reason ?? item.description
                            )}</p>`
                            : ""
                    }
                </article>
            `;
        }).join("");

        container.innerHTML = `
            <div class="section-description">
                These are data-driven planning recommendations based on scheduled service
                intensity. They do not automatically change published timetables.
            </div>

            <div class="data-grid">
                ${cards}
            </div>
        `;

    } catch (error) {
        console.error("Optimization loading failed:", error);

        showError(
            container,
            "Unable to load schedule optimization data. Check the /api/optimization endpoint."
        );
    }
}


/* ========================= PRIORITY STATIONS ========================= */

async function loadPriorityStations() {
    const container = document.getElementById("stations-content");

    if (!container) {
        console.warn("Element #stations-content was not found.");
        return;
    }

    showLoading(container, "Loading station monitoring recommendations...");

    try {
        const response = await fetchAPI(API_ENDPOINTS.priorityStations);
        const records = asArray(response);

        if (!records.length) {
            container.innerHTML = renderEmpty(
                "No station monitoring recommendations are available."
            );
            return;
        }

        const sortedRecords = [...records].sort((a, b) =>
            Number(
                b.average_service_pressure ??
                b.service_pressure_score ??
                0
            ) -
            Number(
                a.average_service_pressure ??
                a.service_pressure_score ??
                0
            )
        );

        const cards = sortedRecords.slice(0, 100).map((item, index) => {
            const stopName = getStopName(item);
            const stopId = getValue(item, ["stop_id"]);
            const route = getRouteName(item);

            const recommendation = getValue(item, [
                "recommendation_category",
                "optimization_category",
                "priority_category",
                "category",
                "recommendation"
            ], "MONITOR_STOP_ACTIVITY");

            const averagePressure =
                item.average_service_pressure ??
                item.service_pressure_score;

            const maximumPressure =
                item.maximum_service_pressure ??
                item.max_service_pressure ??
                item.max_service_pressure_score;

            return `
                <article class="data-card">
                    <h4>
                        ${index + 1}. ${escapeHTML(stopName)}
                    </h4>

                    ${makePill(
                        recommendation,
                        getCategoryClass(recommendation)
                    )}

                    ${renderDataRow("Stop ID", String(stopId))}
                    ${renderDataRow("Route", String(route))}

                    ${renderDataRow(
                        "Average service pressure",
                        averagePressure !== undefined
                            ? formatPressure(averagePressure)
                            : "N/A"
                    )}

                    ${renderDataRow(
                        "Maximum service pressure",
                        maximumPressure !== undefined
                            ? formatPressure(maximumPressure)
                            : "N/A"
                    )}
                </article>
            `;
        }).join("");

        container.innerHTML = `
            <p class="section-description">
                Stations are ordered by their available service-pressure score.
                Priority labels are planning recommendations, not direct passenger counts.
            </p>

            <div class="data-grid">
                ${cards}
            </div>
        `;

    } catch (error) {
        console.error("Priority station loading failed:", error);

        showError(
            container,
            "Unable to load priority stations. Check the /api/priority-stops endpoint."
        );
    }
}


/* ========================= DELAY MODEL ========================= */

async function loadDelayModel() {
    const statusElement =
        document.getElementById("overview-delay-status");

    const descriptionElement =
        document.getElementById("overview-delay-description");

    const placeholder = document.querySelector(".delay-placeholder");
    const rulesContainer = document.querySelector(".delay-rules");

    const pill = document.querySelector(
        ".pill.waiting"
    );

    try {
        const data = await fetchAPI(API_ENDPOINTS.delayModel);

        const status = normalizeCategory(
            getValue(data, ["status"], "UNKNOWN")
        );

        const observations = getValue(
            data,
            ["historical_observations", "observation_count"],
            0
        );

        const trips = getValue(
            data,
            ["unique_trips", "trip_count"],
            0
        );

        const operationalReady =
            data.prediction_ready_for_operational_use === true;

        let statusLabel = "NOT AVAILABLE";
        let description =
            "Delay prediction information is currently unavailable.";

        if (status === "TRAINED_PRELIMINARY") {
            statusLabel = "TRAINED — PRELIMINARY";
            description =
                `The preliminary delay model was trained using ${number(observations)} ` +
                `historical observations from ${number(trips)} unique trips. ` +
                "Its current evaluation does not establish reliable operational accuracy.";
        } else if (
            status === "READY" ||
            status === "TRAINED"
        ) {
            statusLabel = operationalReady
                ? "MODEL READY"
                : "TRAINED — VALIDATION REQUIRED";

            description = operationalReady
                ? "The backend reports the model as ready."
                : "A trained model is available, but operational reliability has not been confirmed.";
        } else if (
            status === "WAITING_FOR_DATA" ||
            status === "WAITING"
        ) {
            statusLabel = "WAITING FOR REAL DELAY DATA";
            description =
                "The system needs sufficient matched real-time and scheduled data before model training.";
        } else {
            statusLabel = status.replace(/_/g, " ");
            description = getValue(
                data,
                ["evaluation_note", "message"],
                description
            );
        }

        if (statusElement) {
            statusElement.textContent = statusLabel;
        }

        if (descriptionElement) {
            descriptionElement.textContent = description;
        }

        if (pill) {
            pill.textContent = statusLabel;
            pill.classList.remove("waiting", "success", "danger");

            pill.classList.add(
                operationalReady ? "success" : "waiting"
            );
        }

        const stationPredictions = Array.isArray(data.station_predictions)
            ? data.station_predictions
            : [];

        if (placeholder) {
            const stationCards = stationPredictions.map(station => {
                const predictedDelay = Number(station.predicted_delay_minutes);
                const historicalDelay = Number(station.historical_delay_minutes);
                const predictedText = Number.isFinite(predictedDelay)
                    ? `${number(predictedDelay, 2)} minutes`
                    : "Not available";
                const historicalText = Number.isFinite(historicalDelay)
                    ? `${number(historicalDelay, 2)} minutes`
                    : "Not available";

                return renderDataCard(
                    getValue(station, ["station_name"], "Unknown station"),
                    [
                        renderDataRow("Experimental delay estimate", predictedText),
                        renderDataRow("Recorded historical delay", historicalText),
                        renderDataRow(
                            "Historical trip",
                            String(getValue(station, ["trip_id"], "N/A"))
                        )
                    ],
                    "PRELIMINARY ESTIMATE"
                );
            }).join("");

            placeholder.innerHTML = `
                <p class="section-description">
                    ${escapeHTML(description)}
                </p>

                <section class="delay-prediction-results">
                    <h3>Experimental Station Delay Estimates</h3>
                    ${stationCards
                        ? `<div class="data-grid">${stationCards}</div>`
                        : renderEmpty(
                            data.prediction_error
                                ? `Station estimates could not be generated: ${data.prediction_error}`
                                : "No station estimates are currently available."
                        )}
                </section>

                <p class="section-description">
                    ${escapeHTML(
                        getValue(
                            data,
                            ["evaluation_note"],
                            "These estimates are preliminary and are not validated live forecasts."
                        )
                    )}
                </p>
            `;
        }

        if (rulesContainer) {
            rulesContainer.innerHTML = `
                <div class="data-grid">
                    ${renderDataCard("Model Status", [
                        renderDataRow("Status", statusLabel),
                        renderDataRow(
                            "Historical observations",
                            number(observations)
                        ),
                        renderDataRow(
                            "Unique trips",
                            number(trips)
                        ),
                        renderDataRow(
                            "Trained model available",
                            data.trained_model_available ? "Yes" : "No"
                        ),
                        renderDataRow(
                            "Historical target available",
                            data.historical_delay_target_available ? "Yes" : "No"
                        ),
                        renderDataRow(
                            "Artificial labels used",
                            data.artificial_labels_used ? "Yes" : "No"
                        ),
                        renderDataRow(
                            "Operational use",
                            operationalReady ? "Approved by model status" : "Not validated"
                        )
                    ])}
                </div>

                <p class="section-description">
                    ${escapeHTML(
                        getValue(
                            data,
                            ["evaluation_note"],
                            "Model results are preliminary and should not be treated as validated operational predictions."
                        )
                    )}
                </p>
            `;
        }

    } catch (error) {
        console.error("Delay model loading failed:", error);

        if (statusElement) {
            statusElement.textContent = "MODEL STATUS UNAVAILABLE";
        }

        if (descriptionElement) {
            descriptionElement.textContent =
                "Could not retrieve delay model information from the backend.";
        }

        if (placeholder) {
            placeholder.textContent =
                "Could not retrieve delay model information from the backend.";
        }

        if (rulesContainer) {
            rulesContainer.innerHTML = renderEmpty(
                "Delay model details could not be loaded."
            );
        }
    }
}


/* ========================= OPTIONAL ROUTE AND STOP DATA ========================= */

async function loadRoutes() {
    try {
        const response = await fetchAPI(API_ENDPOINTS.routes);
        const records = asArray(response);

        const container = document.getElementById("routes-content");

        if (!container) return;

        if (!records.length) {
            container.innerHTML = renderEmpty("No route records available.");
            return;
        }

        container.innerHTML = `
            <div class="data-grid">
                ${records.slice(0, 100).map(item =>
                    renderDataCard(
                        getValue(item, [
                            "route_long_name",
                            "route_name",
                            "route_short_name",
                            "route_id"
                        ], "Route"),
                        [
                            renderDataRow(
                                "Route ID",
                                String(getValue(item, ["route_id"]))
                            ),
                            renderDataRow(
                                "Route type",
                                String(getValue(item, ["route_type"]))
                            )
                        ]
                    )
                ).join("")}
            </div>
        `;

    } catch (error) {
        console.error("Route loading failed:", error);
    }
}


async function loadStops() {
    try {
        const response = await fetchAPI(API_ENDPOINTS.stops);
        const records = asArray(response);

        const container = document.getElementById("stops-content");

        if (!container) return;

        if (!records.length) {
            container.innerHTML = renderEmpty("No stop records available.");
            return;
        }

        container.innerHTML = `
            <div class="data-grid">
                ${records.slice(0, 100).map(item =>
                    renderDataCard(
                        getStopName(item),
                        [
                            renderDataRow(
                                "Stop ID",
                                String(getValue(item, ["stop_id"]))
                            ),
                            renderDataRow(
                                "Latitude",
                                String(getValue(item, ["stop_lat"]))
                            ),
                            renderDataRow(
                                "Longitude",
                                String(getValue(item, ["stop_lon"]))
                            )
                        ]
                    )
                ).join("")}
            </div>
        `;

    } catch (error) {
        console.error("Stop loading failed:", error);
    }
}


/* ========================= INITIALIZATION ========================= */

async function initializeDashboard() {
    initializeNavigation();

    // Load each section independently so one failed endpoint
    // does not prevent the other sections from loading.
    await Promise.allSettled([
        loadHealth(),
        loadSummary(),
        loadCrowdData(),
        loadOptimizationData(),
        loadPriorityStations(),
        loadDelayModel()
    ]);
}


/* ========================= START APPLICATION ========================= */

if (document.readyState === "loading") {
    document.addEventListener(
        "DOMContentLoaded",
        initializeDashboard
    );
} else {
    initializeDashboard();
}