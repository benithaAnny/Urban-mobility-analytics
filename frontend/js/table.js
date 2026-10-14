// Trip table: sorting, pages and a detail pop-up.
// Sorting and paging happen in the database, so only 25 rows are sent at a time.
import { get } from "./api.js";
import { fmt, escapeHtml } from "./format.js";
import { showError } from "./panels.js";

const PAGE_SIZE = 25;
const table = {
    sort: "pickup_datetime",
    order: "desc",
    page: 1,
    total: 0,
    getFilters: null,
};

export function setupTripTable(getFilters) {
  table.getFilters = getFilters;
    document.querySelectorAll("#trips-table th[data-sort]").forEach((header) => {
        header.addEventListener("click", () => changeSort(header.dataset.sort));
    });
    document.getElementById("prev-page").addEventListener("click", () => {
        loadTrips(table.page - 1).catch((error) => showError(error.message));
    });
    document.getElementById("next-page").addEventListener("click", () => {
        loadTrips(table.page + 1).catch((error) => showError(error.message));
    });
    document.querySelector("#trips-table tbody").addEventListener("click", (event) => {
        const row = event.target.closest("tr[data-id]");
        if (row) showTrip(row.dataset.id);
    });
    document.getElementById("modal-close").addEventListener("click", closeTrip);
    document.getElementById("trip-modal").addEventListener("click", (event) => {
        if (event.target.id === "trip-modal") closeTrip();
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeTrip();
    });
}

function changeSort(column) {
  if (table.sort === column) {
    table.order = table.order === "desc" ? "asc" : "desc";
    } else {
    table.sort = column;
    table.order = "desc";
    }
    loadTrips(1).catch((error) => showError(error.message));
}

export async function loadTrips(page) {
    if (page < 1) return;
    const params = { ...table.getFilters(), sort: table.sort, order: table.order, page: page, page_size: PAGE_SIZE };
    const data = await get("/trips", params);
    table.page = data.page;
    table.total = data.total;
    showTrips(data.rows);
}

function showTrips(rows) {
  // Highlight the sorted column and show an arrow
    document.querySelectorAll("#trips-table th[data-sort]").forEach((header) => {
        const name = header.textContent.replace(" \u2191", "").replace(" \u2193", "");
        if (header.dataset.sort === table.sort) {
            header.classList.add("sorted");
            header.textContent = name + (table.order === "desc" ? " \u2193" : " \u2191");
        } else {
            header.classList.remove("sorted");
            header.textContent = name;
        }
    });

    const body = document.querySelector("#trips-table tbody");
        if (rows.length === 0) {
            body.innerHTML = '<tr><td colspan="10" class="empty">No trips match these filters.</td></tr>';
        } else {
            let html = "";
                for (const row of rows) {
                    const flag = row.is_suspicious ? ' class="suspicious" title="Flagged by the pipeline"' : "";
                    html += '<tr data-id="' + row.trip_id + '"' + flag + ">" +
                        "<td>" + escapeHtml(row.pickup_datetime) + "</td>" +
                        "<td>" + escapeHtml(row.pickup_zone) + "</td>" +
                        "<td>" + escapeHtml(row.dropoff_zone) + "</td>" +
                        "<td>" + fmt.num(row.trip_distance, 2) + "</td>" +
                        "<td>" + fmt.num(row.duration_min) + "</td>" +
                        "<td>" + fmt.num(row.avg_speed_mph) + "</td>" +
                        "<td>" + fmt.money(row.total_amount) + "</td>" +
                        "<td>" + fmt.money(row.fare_per_mile) + "</td>" +
                        "<td>" + fmt.pct(row.tip_pct) + "</td>" +
                        "<td>" + escapeHtml(row.payment) + "</td></tr>";
                }
                    body.innerHTML = html;
        }

        const pages = Math.max(1, Math.ceil(table.total / PAGE_SIZE));
        document.getElementById("page-info").textContent = "Page " + fmt.int(table.page) + " of " + fmt.int(pages);
        document.getElementById("trip-count").textContent = fmt.int(table.total) + " matching trips";
        document.getElementById("prev-page").disabled = table.page <=1;
        document.getElementById("next-page").disabled = table.page >= pages;
}

async function showTrip(id) {
    try {
        const trip = await get("/trips/" + id);
        const extras = trip.extra + trip.mta_tax + trip.improvement_surcharge +
                       trip.congestion_surcharge + trip.airport_fee + trip.cbd_congestion_fee;
        let tip = fmt.money(trip.tip_amount);
        if (trip.tip_pct !== null) tip += " (" + fmt.pct(trip.tip_pct) + ")";
        let passengers = String(trip.passenger_count);
        if (trip.passenger_imputed) passengers += " (repaired)";

        const fields = [
            ["Pickup", escapeHtml(trip.pickup_datetime)],
            ["Drop-off", escapeHtml(trip.dropoff_datetime)],
            ["Distance", fmt.num(trip.trip_distance, 2) + " mi"],
            ["Duration", fmt.num(trip.duration_min) + " min"],
            ["Average speed", fmt.num(trip.avg_speed_mph) + " mph"],
            ["Time of day", escapeHtml(trip.time_band)],
            ["Passengers", passengers],
            ["Vendor", escapeHtml(trip.vendor)],
            ["Rate code", escapeHtml(trip.rate_code)],
            ["Payment", escapeHtml(trip.payment)],
            ["Fare", fmt.money(trip.fare_amount)],
            ["Extras & surcharges", fmt.money(extras)],
            ["Tolls", fmt.money(trip.tolls_amount)],
            ["Tip", tip],
            ["Total", "<b>" + fmt.money(trip.total_amount) + "</b>"],
            ["Fare per mile", fmt.money(trip.fare_per_mile)],
        ];
        let grid = "";
        for (const [label, value] of fields) {
            grid += "<div><span>" + label + "</span>" + value + "</div>";
        }

        let warning = "";
        if (trip.is_suspicious) {
            warning = '<p class="warn">Flagged: The bill items don\'t add up, or the tip is bigger than the fare.</p>';
        }

        document.getElementById("modal-body").innerHTML =
            "<h2>Trip #" + trip.trip_id + "</h2>" +
            "<p>" + escapeHtml(trip.pickup_zone) + " (" + escapeHtml(trip.pickup_borough) + ") &rarr; " +
            warning + '<div class="detail-grid">' + grid + "</div>";
        document.getElementById("trip-modal").hidden = false;
    } catch (error) {
        showError(error.message);
    }
}

function closeTrip() {
    document.getElementById("trip-modal").hidden = true;
}
        