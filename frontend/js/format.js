// Number formatting and safe HTML text.

function isMissing(value) {
    return value === null || value === undefined ||Number.isNaN(Number(value));
}
const wholeNumber = new Intl.NumberFormat("en-US");
const shortNumber = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });

export const fmt = {
    int: (v) => (isMissing(v) ? "-" : wholeNumber.format(Math.round(v))),
    num: (v, decimals = 1) => (isMissing(v) ? "-" : Number(v).toFixed(decimals)),
    money: (v) => (isMissing(v) ? "-" : "$" + Number(v).toFixed(2)),
    pct: (v) => (isMissing(v) ? "-" : Number(v).toFixed(1) + "%"),
    compact: (v) => (isMissing(v) ? "-" : shortNumber.format(v)),
    hour: (h) => String(h).padStart(2, "0") + ":00",
};

export const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

// Make text safe to put inside HTML (stops zone names breaking the page)
export function escapeHtml(value) {
    const text = value === null || value === undefined ? "" : String(value);
    return text
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}
        
        
        
        

