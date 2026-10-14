// Fills the KPI cards, insight sentences, heatmap, rankings and data-quality table.
import { fmt, DAYS, escapeHtml } from "./format.js";
import { metricLabel } from "./map.js";

export function showError(message) {
  const box = document.createElement("div");
  box.className = "toast";
  box.textContent = message;
  document.body.appendChild(box);
  setTimeout(() => box.remove(), 5000);
}

export function showKpis(summary) {
  const cards = [
    ["Trips", fmt.int(summary.trips)],
    ["Avg total fare", fmt.money(summary.avg_total)],
    ["Avg distance", fmt.num(summary.avg_distance, 2) + " mi"],
    ["Avg duration", fmt.num(summary.avg_duration) + " min"],
    ["Average speed", fmt.num(summary.avg_speed) + " mph"],
    ["Fare per mile", fmt.money(summary.fare_per_mile)],
    ["Avg card tip", fmt.pct(summary.avg_tip_pct)],
    ["Revenue", "$" + fmt.compact(summary.revenue)],
  ];
  let html = "";
  for (const [label, value] of cards) {
    html += '<div class="kpi"><div class="label">' + label + '</div><div class="value">' + value + "</div></div>";
  }
  document.getElementById("kpis").innerHTML = html;
}

// Find the row with the biggest (or smallest) value
function biggest(rows, field) {
  let best = rows[0];
  for (const row of rows) if (row[field] > best[field]) best = row;
  return best;
}
function smallest(rows, field) {
  let best = rows[0];
  for (const row of rows) if (row[field] < best[field]) best = row;
  return best;
}

// Every sentence is calculated from the current data, so it stays true for any filter.
export function showInsights(data) {
  const list = document.getElementById("insights");
  if (!data.summary.trips) {
    list.innerHTML = "<li>No trips match these filters.</li>";
    return;
  }
  const sentences = [];

  // Ignore hours with very few trips when comparing speeds
  const busyHours = data.hourly.filter((row) => row.trips >= data.summary.trips * 0.01);
  if (busyHours.length > 1) {
    const peak = biggest(data.hourly, "trips");
    const slowest = smallest(busyHours, "avg_speed");
    const fastest = biggest(busyHours, "avg_speed");
    sentences.push("Demand peaks at <b>" + fmt.hour(peak.hour) + "</b> (" + fmt.int(peak.trips) +
      " trips). Traffic is slowest at <b>" + fmt.hour(slowest.hour) + "</b> at " + fmt.num(slowest.avg_speed) +
      " mph, compared with " + fmt.num(fastest.avg_speed) + " mph at " + fmt.hour(fastest.hour) + ".");
  }

  if (data.zones.length > 0) {
    const top = data.zones[0];
    sentences.push("<b>" + escapeHtml(top.zone) + "</b> (" + escapeHtml(top.borough) +
      ") is the busiest pickup zone, starting " + fmt.pct(top.trips / data.summary.trips * 100) + " of all trips.");
  }

  if (data.distance.length > 1) {
    const shortest = data.distance[0];
    const longest = data.distance[data.distance.length - 1];
    sentences.push(shortest.band + " mile trips cost <b>" + fmt.money(shortest.fare_per_mile) +
      "</b> per mile in fare, against " + fmt.money(longest.fare_per_mile) + " for " + longest.band +
      " mile trips: fixed charges weigh most on short trips.");
  }

  const card = data.payment.find((row) => row.payment_type_id === 1);
  const cash = data.payment.find((row) => row.payment_type_id === 2);
  if (card && cash) {
    sentences.push(fmt.pct(card.pct_with_tip) + " of card trips record a tip, but only " +
      fmt.pct(cash.pct_with_tip) + " of cash trips do. Cash tips are not recorded by the meter, " +
      "so tip analysis uses card trips only.");
  }

  list.innerHTML = sentences.map((text) => "<li>" + text + "</li>").join("");
}

export function showHeatmap(rows) {
  // 7 days x 24 hours, all starting at 0
  const grid = [];
  for (let day = 0; day < 7; day++) grid.push(new Array(24).fill(0));
  let max = 0;
  for (const row of rows) {
    grid[row.dow][row.hour] = row.trips;
    if (row.trips > max) max = row.trips;
  }

  let html = "<div></div>";
  for (let hour = 0; hour < 24; hour++) {
    html += '<div class="hlabel">' + (hour % 3 === 0 ? hour : "") + "</div>";
  }
  for (let day = 0; day < 7; day++) {
    html += '<div class="dlabel">' + DAYS[day] + "</div>";
    for (let hour = 0; hour < 24; hour++) {
      const trips = grid[day][hour];
      const brightness = max ? (0.06 + 0.94 * trips / max).toFixed(2) : 0.06;
      html += '<div class="cell" style="opacity:' + brightness + '" title="' +
              DAYS[day] + " " + fmt.hour(hour) + ": " + fmt.int(trips) + ' trips"></div>';
    }
  }
  document.getElementById("heatmap").innerHTML = html;
}

function formatMetric(value, metric) {
  if (metric === "trips") return fmt.int(value) + " trips";
  if (metric === "avg_speed") return fmt.num(value) + " mph";
  if (metric === "fare_per_mile") return fmt.money(value) + "/mi";
  return fmt.pct(value);
}

export function showTopZones(rows, metric, onZoneClick) {
  document.getElementById("top-title").textContent = metricLabel(metric);
  const list = document.getElementById("top-zones");
  if (rows.length === 0) {
    list.innerHTML = '<li class="muted">No zones with enough trips.</li>';
    return;
  }
  let html = "";
  for (const row of rows) {
    let details = escapeHtml(row.borough) + " - " + formatMetric(row[metric], metric);
    if (metric !== "trips") details += " - " + fmt.int(row.trips) + " trips";
    html += '<li><a href="#" data-id="' + row.location_id + '">' + escapeHtml(row.zone) + "</a><span>" + details + "</span></li>";
  }
  list.innerHTML = html;
  list.querySelectorAll("a[data-id]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      onZoneClick(Number(link.dataset.id));
    });
  });
}

export function showRoutes(rows) {
  const body = document.querySelector("#routes-table tbody");
  if (rows.length === 0) {
    body.innerHTML = '<tr><td colspan="7" class="empty">No routes match these filters.</td></tr>';
    return;
  }
  let html = "";
  rows.forEach((row, index) => {
    html += "<tr><td>" + (index + 1) + "</td>" +
      "<td>" + escapeHtml(row.pickup_zone) + ' <span class="muted small">' + escapeHtml(row.pickup_borough) + "</span></td>" +
      "<td>" + escapeHtml(row.dropoff_zone) + ' <span class="muted small">' + escapeHtml(row.dropoff_borough) + "</span></td>" +
      "<td>" + fmt.int(row.trips) + "</td><td>" + fmt.num(row.avg_duration) + "</td>" +
      "<td>" + fmt.num(row.avg_speed) + "</td><td>" + fmt.money(row.avg_total) + "</td></tr>";
  });
  body.innerHTML = html;
}

export function showQuality(rows) {
  let html = "";
  for (const row of rows) {
    html += "<tr><td><code>" + escapeHtml(row.reason) + "</code></td>" +
      '<td><span class="badge ' + escapeHtml(row.action) + '">' + escapeHtml(row.action) + "</span></td>" +
      "<td>" + fmt.int(row.record_count) + '</td><td class="wrap">' + escapeHtml(row.description) + "</td></tr>";
  }
  document.querySelector("#quality-table tbody").innerHTML = html;
}
