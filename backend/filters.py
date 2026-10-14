from datetime import date

FILTERS = {
    "start_date":    ("t.pickup_date  >= ?", "date", None, None),
    "end_date":      ("t.pickup_date  <= ?", "date", None, None),
    "borough":       ("t.pu_location_id IN (SELECT z.location_id FROM zones z "
                      "JOIN boroughs b ON b.borough_id = z.borough_id WHERE b.name = ?)",
                      "text", None, None),
    "pu_zone":       ("t.pu_location_id = ?", "int", 1, 9999),
    "do_zone":       ("t.do_location_id =?",  "int", 1 ,9999),
    "hour_min":      ("t.pickup_hour  >=?", "int", 0, 23),
    "hour_max":      ("t.pickup_hour   <=?", "int", 0, 23),
    "min_distance":  ("t.trip_distance  >=?", "float", 0, None),
    "max_distance":  ("t.trip_distance  <=?", "float", 0, None),
    "min_fare":      ("t.total_amount  >=?", "float", 0, None),
    "max_fare":      ("t.total_amount  <=?", "float", 0, None),
    "payment_type":  ("t.payment_type_id = ?", "int", 0, 99),
    "time_band":     ("t.time_band = ?", "text", None,None),
    "weekend":       ("t.is_weekend = ?", "int", 0, 1),
    "airport":       ("t.is_airport  =?", "int", 0, 1),

}

def check_value(text, value_type, smallest, largest):
    if value_type == "text":
        return text
    if value_type == "date":
        date.fromisoformat(text)
        return text
    if value_type == "int":
        value = int(text)

    else:
        value = float(text)
    if smallest is not None and value <smallest:
        raise ValueError
    if largest is not None and value > largest:
        raise ValueError
    return value

def build_where(args):
    conditions = []
    values = []
    for name, (condition, value_type, smallest, largest) in FILTERS.items():
        text = args.get(name, "").strip()
        if text == "":
            continue
        try:
            value = check_value(text,value_type, smallest, largest)
        except ValueError:
            raise ValueError(f"Invalid value for '{name}': {text}")
        conditions.append(condition)
        values.append(value)
    if not conditions:
        return "", []
    return "WHERE " + " AND ".join(conditions), values