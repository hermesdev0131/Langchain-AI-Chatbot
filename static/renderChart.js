// renderChart.js

document.addEventListener("DOMContentLoaded", () => {
    const unifiedColor = window.UNIFIED_COLOR
    const ctx = document.getElementById("analyticsChart").getContext("2d");

    // Create a single global Chart instance with your original advanced config
    window.currentChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "Frequency over Time",
                data: [],
                fill: false,
                borderColor: unifiedColor,
                backgroundColor: unifiedColor,
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 5,        // Keep the bigger point radius
                pointHoverRadius: 7    // Keep the bigger hover radius
            }]
        },
        options: {
            plugins: {
                tooltip: {
                    enabled: true,
                    mode: "index",
                    intersect: false,
                    callbacks: {
                        label: context => {
                            return context.dataset.label + ": " + context.parsed.y;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: "time",
                    time: {
                        unit: false,
                        displayFormats: {
                            millisecond: 'MMM dd, yyyy, h:mm:ss.SSS a',
                            second: 'MMM dd, yyyy, h:mm:ss a',
                            minute: 'MMM dd, yyyy, h:mm a',
                            hour: 'MMM dd, yyyy, h',
                            day: 'MMM dd, yyyy',
                            week: 'MMM dd, yyyy',
                            month: 'MMM yyyy',
                            quarter: '[Q]Q - yyyy',
                            year: 'yyyy'
                        },
                        tooltipFormat: "MMM dd, yyyy, h:mm:ss a"
                    },
                    title: {
                        display: true,
                        text: "Time"
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Frequency"
                    }
                }
            }
        }
    });

    // Attach "Enter key" listeners to your search inputs
    ["searchTerm", "limitInput", "radiusInput"].forEach(id => {
        const inputEl = document.getElementById(id);
        inputEl.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                searchAndUpdate();
            }
        });
    });
});

// Async fetch function
async function fetchSearchData(term, limit, radius) {
    const queryUrl = `/api/data_search?query=${encodeURIComponent(term)}&limit=${limit}&radius=${radius}`;
    const response = await fetch(queryUrl);
    if (!response.ok) {
        throw new Error("Failed to fetch search data");
    }
    return response.json();
}

// Update chart data in place instead of destroying/re-creating
function updateTimelineChart(labels, values) {
    const chart = window.currentChart;
    if (!chart) return;

    chart.data.labels = labels;
    chart.data.datasets[0].data = values;
    chart.update(); // Re-render with new data/labels
}

// Main search routine
async function searchAndUpdate() {
    const term = document.getElementById("searchTerm").value.trim();
    if (!term) return;

    // Use user-provided limit/radius or defaults
    const limitVal = document.getElementById("limitInput").value;
    const radiusVal = document.getElementById("radiusInput").value;
    const limit = limitVal ? parseInt(limitVal, 10) : 100;
    const radius = radiusVal ? parseFloat(radiusVal) : 0.8;

    try {
        const searchResult = await fetchSearchData(term, limit, radius);
        console.log("Full aggregated search result:", searchResult);

        // Expecting { frequency: totalFrequency, result: [ { datetime, frequency }, ... ] }
        const aggregated = searchResult.result;
        const labels = aggregated.map(row => new Date(row.datetime));
        const values = aggregated.map(row => row.frequency);

        // Update existing chart
        updateTimelineChart(labels, values);

    } catch (error) {
        console.error("Error during search:", error);
    }
}
