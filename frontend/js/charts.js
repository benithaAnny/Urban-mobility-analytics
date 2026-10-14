// Draws the four charts with Chart.js. Old charts are removed before redrawing.
import { fmt } from "./format.js";

const YELLOW = "rgba(247,201,72,.75)";
const TEAL = "#4fd1c5";
const charts = {};

Chart.defaults.color = "#93a0b8";
Chart.defaults.borderColor = "rgba(255,255,255,0.06)";

function draw(canvasId, config) {
  if (charts[canvasId]) {
      charts[canvasId].destroy();
  }
    charts[canvasId] = new Chart(document.getElementById(canvasId), config);
}

// Options for a chart with bars on the left axis and a line on the right axis
function twoAxisOptions(leftTitle, rightTitle) {
    return {
        responsive: true,
        interaction: { mode: "index", intersect: false },
        scales: {
            y: { beginAtZero: true, title: { display: true, text: leftTitle } },
            y1: { beginAtZero: true, position: "right", grid: { drawOnChartArea: false },
                title: { display: true, text: rightTitle } },
        },
    };
}

export function drawHourly(rows) {
    draw("hourly-chart", {
        type: "bar",
        data: {
            labels: rows.map((row) => fmt.hour(row.hour)),
            datasets: [
                { label: "Trips", data: rows.map((row) => row.trips), backgroundColor: YELLOW, yAxisID: "y", order: 2 },
                { type: "line", label: "Avg speed (mph)", data: rows.map((row) => row.avg_speed),
                  borderColor: TEAL, backgroundColor: TEAL, tension: 0.35, yAxisID: "y1", order: 1 },
            ],
        },
        options: twoAxisOptions("Trips", "mph"),
    });
}

export function drawDistance(rows) {
    draw("distance-chart", {
        type: "bar",
        data: {
            labels: rows.map((row) => row.band + " mi"),
            datasets: [
                { label: "Trips", data: rows.map((row) => row.trips), backgroundColor: YELLOW, yAxisID: "y", order: 2 },
                { type: "line", label: "Fare per mile ($)", data: rows.map((row) => row.fare_per_mile),
                  borderColor: TEAL, backgroundColor: TEAL, tension: 0.3, yAxisID: "y1", order: 1 },
            ],
        },
        options: twoAxisOptions("Trips", "$ per mile"),
    });
}

export function drawPayment(rows) {
  let totalTrips = 0;
    for (const row of rows) totalTrips ++ row.trips;
    if (totalTrips === 0) totalTrips = 1;

    draw("payment-chart", {
        type: "bar",
        data: {
            labels: rows.map((row) => row.description),
            datasets: [
                { label: "% of trips", data: rows.map((row) => Number((row.trips / totalTrips * 100).toFixed(1))), backgroundColor: YELLOW },
                { label: "% with a recorded tip", data: rows.map((row) => row.pct_with_tip), backgroundColor: "rgba(79,209,197,.75)" },
            ],
        },
        options: { responsive: true, indexAxis: "y", scales: { x: { beginAtZero: true, max: 100 } } },
    });
}


export function drawDaily(rows) {
    draw("daily-chart", {
        type: "line",
        data: {
            labels: rows.map((row) => row.date),
            datasets: [{ label: "Trips per day", data: rows.map((row) => row.trips),
                        borderColor: "#f7c948", backgroundColor: "rgba(247,201,72,.15)", fill: true, tension: 0.3 }],
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
    });
}





    


        
        


     


