//Zone Map with Leaflet where each zone is colored by a color according to the chosen measure

import { fmt, escapeHtml } from "./format.js";

const COLOURS = ["#1d2b4a", "#2f4b7c", "#665191", "#a05195", "#d45087", "#f95d6a", "#ffa600"];
const LABELS = {
    trips: "Trips", avg_speed: "Avg speed(mph)", fare_per_mile: "Fare per mile ($)",
    avg_tip_pct: "Avg card tip (%)", avg_total: "Avg total ($)", airport_share: "Airport share (%)",
};

let zoneLayer = null;
let statsByZone = {};
let currentMetric = "trips";
let limits = [];
let onZoneClick = null;

export function metricLabel(metric) {
    return LABELS[metric] || metric;
}

export function initMap(geojson, clickHandler) {
    onZoneClick = clickHandler;
    const map = L.map("map").setView([40.71, -73.95], 10);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors", maxZoom: 18,
    }).addTo(map);

    zoneLayer = L.geoJSON(geojson, {
        style: zoneStyle,
        onEachFeature: (feature, shape) => {
            shape.bindTooltip(tooltipText(feature), {sticky: true});
            shape.on("mouseover", () => shape.setStyle({weight: 2, color: "#ffffff" }));
            shape.on("mouseout", () => zoneLayer.resetStyle(shape));
            shape.on("click", () => onZoneClick(feature.properties.location_id));
        },
    }).addTo(map);

    map.fitBounds(zoneLayer.getBounds());
}

export function updateMap(rows, metric) {
    currentMetric = metric;
    statsByZone = {};
    for(const row of rows) statsByZone[row.location_id] = row;
    limits = groupLimits(rows.map((row)=> row[metric]));
    if (!zoneLayer) return;
    zoneLayer.setStyle(zoneStyle);
    zoneLayer.eachLayer((shape) => shape.setTooltipContent(tooltipText(shape.feature)));
    drawLegend();
}

//function to split sorted values in equal-sized groups and return boundaries
function groupLimits(values) {
    const sorted = values.filter((v) => v !== null && Number.isFinite(v)).sort((a, b) => a - b);
    if (sorted.length === 0) return [];
    const result = [];
    for (let i = 1; i < COLOURS.length; i++) {
        const position = Math.min(sorted.length -1, Math.floor((i * sorted.length) / COLOURS.length));
        result.push(sorted[position]);
    }
    return result;
}

function colourFor(value) {
    if (value === null || value === undefined) return "#141b2b";
    let group = 0;
    while (group <limits.length && value > limits[group]) group ++;
    return COLOURS[group];
}

function zoneStyle(feature) {
    const row = statsByZone[feature.properties.location_id];
    return {
        color: "rgba(255,255,255,.25)",
        weight: 0.6,
        fillColor: colourFor(row ? row[currentMetric] : null),
        fillOpacity: row ? 0.82 : 0.25,
    };
}

function tooltipText(feature) {
    const zone = feature.properties;
    const row = statsByZone[zone.location_id];
    let details = "No trips for the current filters";
    if (row) {
        details = fmt.int(row.trips) + " trips - " + fmt.num(row.avg_speed) + " mph - " +
                  fmt.money(row.fare_per_mile) + "/mi - tip " + fmt.pct(row.avg_tip_pct);

    }
    return "<strong>" + escapeHtml(zone.zone) + "</strong><br><small>" + escapeHtml(zone.borough) + "</small><br>" + details;
}

function drawLegend() {
    const legend = document.getElementById("map-legend");
    if (limits.length === 0) {
        legend.innerHTML = "";
        return;
    }
    const show = (v) => (currentMetric === "trips" ? fmt.compact(v) : fmt.num(v));
    let html = "<strong>" + metricLabel(currentMetric) + ":</strong> ";
    for (let i = 0; i < COLOURS.length; i++) {
        let text;
        if (i === 0) text = "up to " + show(limits[0]);
        else if (i === COLOURS.length -1) text = "over " + show(limits[i - 1]);
        else text = show(limits[i - 1]) + " - " + show(limits[i]);
        html += '<span><i style="background:' + COLOURS[i] + '"></i>' + text + "</span>";
    }
    legend.innerHTML = html;
}