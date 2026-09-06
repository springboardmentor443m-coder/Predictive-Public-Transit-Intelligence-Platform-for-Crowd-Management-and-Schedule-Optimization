// ============================================================
// V/LINE TRANSIT INTELLIGENCE - FRONTEND
// ============================================================

const API_BASE = "http://127.0.0.1:5000";


// ============================================================
// HELPERS
// ============================================================

async function fetchAPI(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`);

    if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
    }

    return await response.json();
}


function formatNumber(value) {
    return Number(value).toLocaleString();
}


function formatPressure(value) {
    return `${(Number(value) * 100).toFixed(1)}%`;
}


// ============================================================
// NAVIGATION
// ============================================================

const navItems = document.querySelectorAll(".nav-item");
const sections = document.querySelectorAll(".dashboard-section");
const pageTitle = document.getElementById("page-title");

const titles = {
    overview: "Network Overview",
    crowd: "Crowd Management",
    optimization: "Schedule Optimization",
    stations: "Priority Stations",
    delay: "Delay Prediction"
};


navItems.forEach(item => {

    item.addEventListener("click", () => {

        const sectionName = item.dataset.section;

        navItems.forEach(nav => {
            nav.classList.remove("active");
        });

        item.classList.add("active");

        sections.forEach(section => {
            section.classList.remove("active");
        });

        const targetSection = document.getElementById(sectionName);

        if (targetSection) {
            targetSection.classList.add("active");
        }

        pageTitle.textContent =
            titles[sectionName] || "Dashboard";

    });

});


// ============================================================
// BACKEND HEALTH
// ============================================================

async function loadHealth() {

    const statusElement =
        document.getElementById("backend-status");

    try {

        const data = await fetchAPI("/api/health");

        if (data.status === "healthy") {

            statusElement.textContent =
                "Backend Connected";

        } else {

            statusElement.textContent =
                "Backend Warning";
        }

    } catch (error) {

        console.error("Health check failed:", error);

        statusElement.textContent =
            "Backend Offline";
    }
}


// ============================================================
// NETWORK SUMMARY
// ============================================================

async function loadSummary() {

    try {

        const data = await fetchAPI("/api/summary");

        document.getElementById("metric-routes").textContent =
            formatNumber(data.routes);

        document.getElementById("metric-stops").textContent =
            formatNumber(data.stops);

        document.getElementById("metric-trips").textContent =
            formatNumber(data.trips);

        document.getElementById("metric-features").textContent =
            formatNumber(data.feature_observations);

    } catch (error) {

        console.error("Summary loading failed:", error);

    }
}


// ============================================================
// CROWD MANAGEMENT
// ============================================================

async function loadCrowdData() {

    const container =
        document.getElementById("crowd-content");

    if (!container) {
        console.error("crowd-content element not found");
        return;
    }

    container.innerHTML =
        `<div class="loading">
            Loading crowd data...
        </div>`;

    try {

        const data = await fetchAPI("/api/crowd");

        if (!Array.isArray(data) || data.length === 0) {

            container.innerHTML =
                `<div class="loading">
                    No crowd data available.
                </div>`;

            return;
        }


        // --------------------------------------------------------
        // REMOVE DUPLICATE OBSERVATIONS
        // --------------------------------------------------------
        //
        // A single observation is identified by:
        // stop + route + scheduled hour
        //
        // This prevents the same station/hour from appearing
        // repeatedly as separate cards.
        // --------------------------------------------------------

        const unique = new Map();

        data.forEach(item => {

            const key = [
                item.stop_id,
                item.route_id,
                item.scheduled_hour
            ].join("|");

            if (!unique.has(key)) {
                unique.set(key, item);
            }

        });


        // --------------------------------------------------------
        // SORT BY HIGHEST SERVICE PRESSURE
        // --------------------------------------------------------

        const sorted = Array.from(unique.values())
            .sort(
                (a, b) =>
                    Number(b.service_pressure_score || 0) -
                    Number(a.service_pressure_score || 0)
            )
            .slice(0, 30);


        // --------------------------------------------------------
        // DISPLAY CROWD CARDS
        // --------------------------------------------------------

        container.innerHTML = sorted.map(item => {

            const pressure =
                Number(item.service_pressure_score || 0);

            const percentage =
                (pressure * 100).toFixed(1);

            const hour =
                Number(item.scheduled_hour);

            const displayHour =
                `${String(hour).padStart(2, "0")}:00`;

            const category =
                item.service_pressure_category || "UNKNOWN";

            const categoryClass =
                category === "HIGH"
                    ? "danger"
                    : category === "LOW"
                        ? "success"
                        : "waiting";


            return `
                <div class="data-card">

                    <h4>
                        ${item.stop_name || "Unknown Stop"}
                    </h4>

                    <div class="data-row">
                        <span>Route</span>
                        <strong>
                            ${item.route_id || "—"}
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Scheduled hour</span>
                        <strong>
                            ${displayHour}
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Peak period</span>
                        <strong>
                            ${item.peak_period || "—"}
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Service pressure</span>
                        <strong>
                            ${percentage}%
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Stop activity</span>
                        <strong>
                            ${item.stop_activity_category || "—"}
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Category</span>

                        <span class="pill ${categoryClass}">
                            ${category}
                        </span>
                    </div>

                </div>
            `;

        }).join("");


    } catch (error) {

        console.error(
            "Crowd data loading failed:",
            error
        );

        container.innerHTML =
            `<div class="loading">
                Unable to load crowd data.
            </div>`;
    }
}


// ============================================================
// SCHEDULE OPTIMIZATION
// ============================================================

async function loadOptimizationData() {

    const container =
        document.getElementById("optimization-content");

    try {

        const data =
            await fetchAPI("/api/optimization");

        if (!Array.isArray(data) || data.length === 0) {

            container.innerHTML =
                `<div class="loading">
                    No optimization recommendations available.
                </div>`;

            return;
        }

        const topRecommendations = data
            .filter(
                item =>
                    item.recommendation !== "NO_CHANGE"
            )
            .slice(0, 9);

        if (topRecommendations.length === 0) {

            container.innerHTML =
                `<div class="loading">
                    No active recommendations.
                </div>`;

            return;
        }

        container.innerHTML =
            topRecommendations.map(item => {

                return `
                    <div class="data-card">

                        <h4>
                            ${item.route_id}
                        </h4>

                        <div class="data-row">
                            <span>Hour</span>
                            <strong>
                                ${item.scheduled_hour}:00
                            </strong>
                        </div>

                        <div class="data-row">
                            <span>Peak period</span>
                            <strong>
                                ${item.peak_period}
                            </strong>
                        </div>

                        <div class="data-row">
                            <span>Trip frequency</span>
                            <strong>
                                ${formatNumber(
                                    item.trip_frequency
                                )}
                            </strong>
                        </div>

                        <div class="data-row">
                            <span>Pressure</span>
                            <strong>
                                ${formatPressure(
                                    item.average_service_pressure
                                )}
                            </strong>
                        </div>

                        <div class="data-row">
                            <span>Recommendation</span>

                            <span class="pill waiting">
                                ${item.recommendation}
                            </span>
                        </div>

                    </div>
                `;

            }).join("");

    } catch (error) {

        console.error(
            "Optimization loading failed:",
            error
        );

        container.innerHTML =
            `<div class="loading">
                Unable to load optimization data.
            </div>`;
    }
}


// ============================================================
// PRIORITY STATIONS
// ============================================================

async function loadPriorityStations() {

    const container =
        document.getElementById("stations-content");

    try {

        const data =
            await fetchAPI("/api/priority-stops");

        if (!Array.isArray(data) || data.length === 0) {

            container.innerHTML =
                `<div class="loading">
                    No priority stations available.
                </div>`;

            return;
        }

        container.innerHTML =
            data.slice(0, 9).map((item, index) => {

                return `
                    <div class="data-card">

                        <h4>
                            #${index + 1}
                            ${item.stop_name}
                        </h4>

                        <div class="data-row">
                            <span>Route</span>
                            <strong>
                                ${item.route_id}
                            </strong>
                        </div>

                        <div class="data-row">
                            <span>Stop ID</span>
                            <strong>
                                ${item.stop_id}
                            </strong>
                        </div>

                        <div class="data-row">
                            <span>Trip frequency</span>
                            <strong>
                                ${formatNumber(
                                    item.stop_trip_frequency
                                )}
                            </strong>
                        </div>

                        <div class="data-row">
                            <span>Average pressure</span>
                            <strong>
                                ${formatPressure(
                                    item.average_service_pressure
                                )}
                            </strong>
                        </div>

                        <div class="data-row">
                            <span>Maximum pressure</span>
                            <strong>
                                ${formatPressure(
                                    item.maximum_service_pressure
                                )}
                            </strong>
                        </div>

                        <div class="data-row">
                            <span>Status</span>

                            <span class="pill danger">
                                PRIORITY MONITORING
                            </span>
                        </div>

                    </div>
                `;

            }).join("");

    } catch (error) {

        console.error(
            "Priority station loading failed:",
            error
        );

        container.innerHTML =
            `<div class="loading">
                Unable to load priority stations.
            </div>`;
    }
}


// ============================================================
// DELAY MODEL STATUS
// ============================================================

async function loadDelayModel() {

    try {

        const data =
            await fetchAPI("/api/delay-model");

        const delaySection =
            document.getElementById("delay");

        const statusPill =
            delaySection.querySelector(".pill.waiting");

        if (!statusPill) {
            return;
        }

        if (data.status === "TRAINED") {

            statusPill.textContent =
                "MODEL STATUS: TRAINED";

            statusPill.classList.remove("waiting");
            statusPill.classList.add("success");

        } else {

            statusPill.textContent =
                "MODEL STATUS: WAITING";
        }

    } catch (error) {

        console.error(
            "Delay model status failed:",
            error
        );
    }
}


// ============================================================
// INITIALIZE DASHBOARD
// ============================================================

async function initializeDashboard() {

    await loadHealth();

    await loadSummary();

    await Promise.all([
        loadCrowdData(),
        loadOptimizationData(),
        loadPriorityStations(),
        loadDelayModel()
    ]);

    console.log(
        "V/Line Transit Intelligence dashboard initialized."
    );
}


initializeDashboard();