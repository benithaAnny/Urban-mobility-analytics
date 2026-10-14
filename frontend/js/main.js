// Starts the dashboard and reloads every panel when the filters change.
import { get } from "./api.js";
import * as charts from "./charts.js";
import { initMap, updateMap } from "./map.js";
import * as panels from "./panels.js";
import { setupTripTable, loadTrips } from "./table.js";
import { fmt, escapeHtml } from "./format.js";

const form = document.getElementById("filter-form");
const state = {
 mapMetric: "trips",
 topOrder: "desc",
 zones: [],
 zoneNames: {},
};

// Read the filter form into {name: value}, skipping empty fields
function currentFilters() {
 const filters = {};
 for (const [name, value] of new FormData(form).entries()) {
    if (String(value).trim() !== "") filters[name] = String(value).trim();
 }
 return filters;
}

function addOptions(select, options) {
 for (const [value, label] of options) {
     const option = document.createElement("option");
     option.value = value;
     option.textContent = label;
     select.appendChild(option);
 }
}
function fillFilterChoices(meta) {
    addOptions(form.elements.borough, meta.boroughs.map((name) => [name, name]));
    addOptions(form.elements.time_band, meta.time_bands.map((name) => [name, name]));
    addOptions(form.elements.payment_type, meta.payment_types.map((p) => [p.id, p.description]));
    form.elements.start_date.min = meta.first_date;
    form.elements.start_date.max = meta.last_date;
    form.elements.end_date.min = meta.first_date;
    form.elements.end_date.max = meta.last_date;
    for (const zone of meta.zones) {
        state.zoneNames[zone.location_id] = zone.zone_name + " (" + zone.borough + ")";
    }
    document.getElementById("period").textContent =
        meta.first_date + " to " + meta.last_date + " - " + fmt.int(meta.total_trips) + " clean trips";
}

// Show which zone is selected, with a button to clear it
function showZoneFilter() {
    const box = document.getElementById("filter-status");
    const zoneId = form.elements.pu_zone.value;
    if (!zoneId) {
        box.innerHTML = "";
        return;
      }
    const name = state.zoneNames[zoneId] || zoneId;
        box.innerHTML = '<span class="chip">Pickup: ' + escapeHtml(name) +
            ' <button type="button" id="clear-zone" aria-label="Clear zone">&times;</button></span>';
        document.getElementById("clear-zone").addEventListener("click", () => {
            form.elements.pu_zone.value = "";
            refresh();
    });
}


function selectZone(zoneId) {
    form.elements.pu_zone.value = zoneId;
    refresh();
}
async function loadTopZones() {
  const params = { ...currentFilters(), metric: state.mapMetric, order: state.topOrder, k: 10, min_trips: 50 };
    const rows = await get("/zones/top", params);
      panels.showTopZones(rows, state.mapMetric, selectZone);
}

async function refresh() {
    const filters = currentFilters();
    document.body.classList.add("busy");
    try {
    // Ask for everything at the same time
        const [summary, hourly, heatmap, distance, payment, daily, zones, routes] = await Promise.all([
            get("/summary", filters),
            get("/stats/hourly", filters),
            get("/stats/heatmap", filters),
            get("/stats/distance", filters),
            get("/stats/payment", filters),
            get("/stats/daily", filters),
            get("/zones/stats", { ...filters, sort: "trips", order: "desc" }),
            get("/routes/top", { ...filters, k: 10 }),
        ]);

        panels.showKpis(summary);
        panels.showInsights({ summary, hourly, distance, payment, zones });
        charts.drawHourly(hourly);
        charts.drawDistance(distance);
        charts.drawPayment(payment);
        charts.drawDaily(daily);
        panels.showHeatmap(heatmap);
        panels.showRoutes(routes);
        state.zones = zones;
        updateMap(zones, state.mapMetric);
        await loadTopZones();
        await loadTrips(1);
        showZoneFilter();
      } catch (error) {
        panels.showError(error.message);
      } finally {
        document.body.classList.remove("busy");
      }
}

// Make a row of toggle buttons: only one is "active" at a time
function setupToggle(containerId, onChoose) {
  const buttons = document.querySelectorAll("#" + containerId + " button");
    buttons.forEach((button) => {
        button.addEventListener("click", () => {
              buttons.forEach((other) => other.classList.remove("active"));
                    button.classList.add("active");
                          onChoose(button);
        });
    });
}

function setupControls() {
  form.addEventListener("submit", (event) => {
      event.preventDefault();
          refresh();
  });
    document.getElementById("reset-btn").addEventListener("click", () => {
        form.reset();
            form.elements.pu_zone.value = "";
                refresh();
    });
      setupToggle("map-metric", (button) => {
          state.mapMetric = button.dataset.metric;
              updateMap(state.zones, state.mapMetric);
                  loadTopZones().catch((error) => panels.showError(error.message));
      });
        setupToggle("top-order", (button) => {
            state.topOrder = button.dataset.order;
                loadTopZones().catch((error) => panels.showError(error.message));
        });
}

async function start() {
  try {
      const meta = await get("/meta");
          fillFilterChoices(meta);

              const shapes = await get("/geo/zones");
                  if (shapes.features.length > 0) {
                        initMap(shapes, selectZone);
                  } else {
                        document.getElementById("map").innerHTML =
                                '<p class="empty">Zone shapes not loaded. Add data/raw/taxi_zones.geojson and rerun the pipeline.</p>';
                  }

                      panels.showQuality(await get("/data-quality"));
                          setupTripTable(currentFilters);
                              setupControls();
                                  await refresh();
  } catch (error) {
      panels.showError(error.message);
          document.getElementById("period").textContent = "Could not load data. Is the database built?";
  }
}

start();