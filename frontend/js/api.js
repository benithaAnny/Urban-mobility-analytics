export function toQuery(params) {
    const query = new URLSearchParams();
    for (const key in params) {
        const value = params[key];
        if (value !== "" && value !== null && value !== undefined) {
            query.append(key, value);
        }
    }
    const text = query.toString();
    return text ? "?" + text : "";
}

export async function get(path, params = {}) {
    const response = await fetch("/api" + path + toQuery(params));
    let body = {};
    try {
        body = await response.json();
    } catch (error) {
        body = {};
    }
    if (!response.ok) {
        throw new Error(body.error || "Request failed (" + response.status + ")");
    }
    return body;
}