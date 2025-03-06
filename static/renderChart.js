// full.js

// Create an empty chart when the page loads
window.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById('analyticsChart').getContext('2d');
    window.currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [], // Initially empty
            datasets: [{
                label: 'Frequency over Time',
                data: [], // Initially empty
                fill: false,
                borderColor: 'rgba(255, 195, 0, 1)',
                backgroundColor: 'rgba(255, 195, 0, 0.5)',
                borderWidth: 2,
                tension: 0.1 // Smooth curve
            }]
        },
        options: {
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'minute', // Change as needed (minute, hour, day)
                        tooltipFormat: 'MMM DD, YYYY, h:mm:ss a'
                    },
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Frequency'
                    }
                }
            }
        }
    });

    // Add event listener to the search input to trigger search on Enter key press
    const searchInput = document.getElementById('searchTerm');
    searchInput.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            searchAndUpdate();
        }
    });
    const limitInput = document.getElementById('limitInput');
    limitInput.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            searchAndUpdate();
        }
    });
    const radiusInput = document.getElementById('radiusInput');
    radiusInput.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            searchAndUpdate();
        }
    });
});

// Fetch search data from the server using term, limit, and radius
async function fetchSearchData(term, limit, radius) {
    // Build the query URL with the dynamic parameters.
    const queryUrl = `/api/search_data?query=${encodeURIComponent(term)}&limit=${limit}&radius=${radius}`;
    const response = await fetch(queryUrl);
    if (!response.ok) {
        throw new Error('Failed to fetch search data');
    }
    return await response.json();
}

// Render the timeline chart with new labels and data values
function renderTimelineChart(labels, values) {
    const ctx = document.getElementById('analyticsChart').getContext('2d');
    if (window.currentChart) {
        window.currentChart.destroy();
    }
    window.currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels, // Array of Date objects
            datasets: [{
                label: 'Frequency over Time',
                data: values, // Frequency values
                fill: false,
                borderColor: 'rgba(255, 195, 0, 1)',
                backgroundColor: 'rgba(255, 195, 0, 0.5)',
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 5,        // Increase point radius for better visibility
                pointHoverRadius: 7    // Increase hover radius for tooltips
            }]
        },
        options: {
            plugins: {
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function (context) {
                            return context.dataset.label + ': ' + context.parsed.y;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'minute', // Adjust the time unit as needed
                        tooltipFormat: 'MMM dd, yyyy, h:mm:ss a'
                    },
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Frequency'
                    }
                }
            }
        }
    });
}

// Called when the user performs a search.
async function searchAndUpdate() {
    const term = document.getElementById('searchTerm').value.trim();
    if (!term) return;

    // Get custom parameters from the input fields, or fallback to defaults
    const limitInput = document.getElementById('limitInput').value;
    const radiusInput = document.getElementById('radiusInput').value;
    const limit = limitInput ? parseInt(limitInput) : 100;
    const radius = radiusInput ? parseFloat(radiusInput) : 0.8;

    try {
        const searchResult = await fetchSearchData(term, limit, radius);
        console.log("Full aggregated search result:", searchResult);

        // Assuming server returns aggregated data as:
        // { frequency: totalFrequency, result: [ { "datetime": "2025-03-04T00:00:00Z", "frequency": X }, ... ] }
        const aggregated = searchResult.result;

        // Convert ISO datetime strings to Date objects
        const labels = aggregated.map(row => new Date(row.datetime));
        const values = aggregated.map(row => row.frequency);

        renderTimelineChart(labels, values);
    } catch (error) {
        console.error("Error during search:", error);
    }
}