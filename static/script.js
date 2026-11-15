
let cChart = null;
let tChart = null;
let timelineChart = null;
let pieChart = null;
let countriesLoaded = false;
let deepCountriesLoaded = false;

// --- PAGE 1: GLOBAL OVERVIEW ---
async function loadDashboard() {
    const country = document.getElementById("countryFilter").value;
    const minSev = document.getElementById("sevFilter").value;

    const res = await fetch(`/api/dashboard-data?country=${encodeURIComponent(country)}&min_sev=${minSev}`);
    const data = await res.json();

    document.getElementById("mTotal").innerText = data.metrics.total_events.toLocaleString();
    document.getElementById("mAvg").innerText = data.metrics.avg_severity + " / 10";
    document.getElementById("mShowing").innerText = data.metrics.filtered_count;

    if (!countriesLoaded) {
        const select = document.getElementById("countryFilter");
        data.countries.forEach(c => {
            if (c !== "All") {
                const opt = document.createElement("option");
                opt.value = c;
                opt.innerText = c;
                select.appendChild(opt);
            }
        });
        countriesLoaded = true;
    }

    // Country Bar Chart
    const cLabels = data.country_stats.map(x => x._id);
    const cValues = data.country_stats.map(x => x.total_events);

    if (cChart) cChart.destroy();

    cChart = new Chart(document.getElementById("countryChart"), {
        type: "bar",
        data: {
            labels: cLabels,
            datasets: [{
                label: "Events",
                data: cValues,
                backgroundColor: "#2563eb",
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: "#64748b" }, grid: { display: false } },
                y: { ticks: { color: "#64748b" }, grid: { color: "#f1f5f9" } }
            }
        }
    });

    // Monthly Trend Line Chart
    const tLabels = data.monthly_trend.map(x => x._id);
    const tValues = data.monthly_trend.map(x => x.avg_severity);

    if (tChart) tChart.destroy();

    tChart = new Chart(document.getElementById("trendChart"), {
        type: "line",
        data: {
            labels: tLabels,
            datasets: [{
                label: "Avg Severity",
                data: tValues,
                borderColor: "#2563eb",
                backgroundColor: "rgba(37, 99, 235, 0.08)",
                borderWidth: 2,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: "#64748b" }, grid: { display: false } },
                y: { ticks: { color: "#64748b" }, grid: { color: "#f1f5f9" } }
            }
        }
    });

    // ML Clusters Table
    const mlBody = document.getElementById("mlTableBody");
    mlBody.innerHTML = "";

    data.ml_clusters.forEach(row => {
        let badgeClass = row.risk_level.includes("High")
            ? "high"
            : (row.risk_level.includes("Medium") ? "medium" : "low");

        mlBody.innerHTML += `<tr>
            <td><strong>${row.country}</strong></td>
            <td>${row.total_severity}</td>
            <td>${row.event_count}</td>
            <td><span class="badge ${badgeClass}">${row.risk_level}</span></td>
        </tr>`;
    });

    // Recent Events Table
    const evBody = document.getElementById("eventsTableBody");
    evBody.innerHTML = "";

    data.events.forEach(ev => {
        evBody.innerHTML += `<tr>
            <td>${ev.date}</td>
            <td>${ev.country}</td>
            <td>${ev.region}</td>
            <td>${ev.type}</td>
            <td>${ev.severity}</td>
            <td>${ev.summary}</td>
        </tr>`;
    });
}

async function submitEvent(e) {
    e.preventDefault();

    const msg = document.getElementById("formMsg");

    const payload = {
        date: document.getElementById("evDate").value,
        country: document.getElementById("evCountry").value,
        region: document.getElementById("evRegion").value,
        type: document.getElementById("evType").value,
        severity: document.getElementById("evSev").value,
        summary: document.getElementById("evSummary").value
    };

    const res = await fetch("/api/add-event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const result = await res.json();

   if (res.ok) {
    if (typeof marked !== "undefined" && typeof DOMPurify !== "undefined") {
        const formattedHTML = marked.parse(data.insight);
        contentEl.innerHTML = DOMPurify.sanitize(formattedHTML);
    } else {
        contentEl.innerText = data.insight;
        console.error("Markdown libraries not loaded!");
    }
} else {
    contentEl.innerText = "Error generating AI insights: " + data.message;
}
}

// --- PAGE 2: COUNTRY DEEP-DIVE ANALYTICS ---
async function loadCountryAnalytics(countryName) {
    document.getElementById("cTitle").innerText = `Country Intelligence: ${countryName}`;

    const res = await fetch(`/api/country-analysis?country=${encodeURIComponent(countryName)}`);
    const data = await res.json();

    // Dropdown ko saari countries se populate karein agar pehle nahi hua
    const select = document.getElementById("deepCountrySelect");

    if (select && select.options.length <= 1) {
        select.innerHTML = "";

        data.countries.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c;
            opt.innerText = c;

            if (c === countryName) opt.selected = true;

            select.appendChild(opt);
        });
    }

    // Baaki metrics aur charts render karne ka code...
    const totalCountryEvents = data.type_stats.reduce(
        (sum, item) => sum + item.count, 0
    );

    document.getElementById("cTotalEvents").innerText = totalCountryEvents.toLocaleString();

    if (data.type_stats.length > 0) {
        document.getElementById("cTopType").innerText = data.type_stats[0]._id;
        document.getElementById("cTopTypeCount").innerText =
            `${data.type_stats[0].count.toLocaleString()} recorded incidents`;
    }

    const months = [...new Set(
        data.monthly_by_type.map(item => item._id.month)
    )].sort();

    if (months.length > 0) {
        document.getElementById("cDateRange").innerText =
            `Time Span: ${months[0]} to ${months[months.length - 1]}`;
    }

    const eventTypes = [...new Set(
        data.monthly_by_type.map(item => item._id.type)
    )];

    const colorMap = {
        "conflict": "#dc2626",
        "protest": "#2563eb",
        "diplomacy": "#16a34a",
        "sanction": "#d97706",
        "election": "#7c3aed"
    };

    const datasets = eventTypes.map(t => {
        const monthlyCounts = months.map(m => {
            const found = data.monthly_by_type.find(
                x => x._id.month === m && x._id.type === t
            );

            return found ? found.count : 0;
        });

        return {
            label: t.toUpperCase(),
            data: monthlyCounts,
            borderColor: colorMap[t] || "#475569",
            backgroundColor: colorMap[t] || "#475569",
            borderWidth: 2.5,
            tension: 0.3,
            fill: false
        };
    });

    // Calculate Rise / Fall indicator for Conflict
    const conflictSeries = datasets.find(d => d.label === "CONFLICT");

    if (conflictSeries && conflictSeries.data.length >= 2) {
        const firstVal = conflictSeries.data[0];
        const lastVal = conflictSeries.data[conflictSeries.data.length - 1];
        const diff = lastVal - firstVal;

        const badgeEl = document.getElementById("cTrendBadge");

        if (diff > 0) {
            badgeEl.innerText = `Increased (+${diff})`;
            badgeEl.style.color = "#dc2626";
        } else {
            badgeEl.innerText = `Decreased (${diff})`;
            badgeEl.style.color = "#16a34a";
        }

        document.getElementById("cTrendDetail").innerText =
            `Armed conflicts: ${firstVal} (${months[0]}) → ${lastVal} (${months[months.length - 1]})`;

    } else {
        document.getElementById("cTrendBadge").innerText = "Stable";
        document.getElementById("cTrendBadge").style.color = "#2563eb";
    }

    // Timeline Chart
    if (timelineChart) timelineChart.destroy();

    timelineChart = new Chart(document.getElementById("typeTimelineChart"), {
        type: "line",
        data: {
            labels: months,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            scales: {
                x: {
                    ticks: { color: "#64748b" },
                    grid: { display: false }
                },
                y: {
                    ticks: { color: "#64748b" },
                    grid: { color: "#f1f5f9" },
                    title: {
                        display: true,
                        text: "Number of Incidents",
                        color: "#64748b"
                    }
                }
            }
        }
    });

    // Doughnut Chart for Breakdown
    if (pieChart) pieChart.destroy();

    pieChart = new Chart(document.getElementById("typePieChart"), {
        type: "doughnut",
        data: {
            labels: data.type_stats.map(x => x._id.toUpperCase()),
            datasets: [{
                data: data.type_stats.map(x => x.count),
                backgroundColor: data.type_stats.map(
                    x => colorMap[x._id] || "#64748b"
                )
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    // Regions Table
    const regBody = document.getElementById("regionTableBody");
    regBody.innerHTML = "";

    data.region_stats.forEach(r => {
        regBody.innerHTML += `<tr>
            <td><strong>${r._id || "Unknown"}</strong></td>
            <td>${r.count.toLocaleString()}</td>
            <td><span class="badge ${r.max_sev >= 7 ? 'high' : 'medium'}">${r.max_sev} / 10</span></td>
        </tr>`;
    });
}

async function fetchAIInsights() {
    const country = document.getElementById("deepCountrySelect")
        ? document.getElementById("deepCountrySelect").value
        : "All";

    const loadingEl = document.getElementById("aiLoading");
    const contentEl = document.getElementById("aiContentBox");

    loadingEl.style.display = "block";
    contentEl.innerText = "";

    try {
        const res = await fetch("/api/ai-insights", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ country: country })
        });

        const data = await res.json();

        loadingEl.style.display = "none";

        if (res.ok) {
            contentEl.innerHTML = marked.parse(data.insight);
        } else {
            contentEl.innerText = "Error generating AI insights: " + data.message;
        }

    } catch (err) {
        loadingEl.style.display = "none";
        contentEl.innerText = "Network error while connecting to Gemini AI.";
    }
}
