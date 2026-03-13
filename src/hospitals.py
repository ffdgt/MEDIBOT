import requests


def find_nearby_hospitals(lat, lon, radius=5000):
    """
    Find hospitals near given coordinates using Overpass API (OpenStreetMap)
    radius is in meters — default 5km
    """
    try:
        overpass_url = "https://overpass-api.de/api/interpreter"

        # Query for hospitals, clinics, doctors near location
        overpass_query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="hospital"](around:{radius},{lat},{lon});
          node["amenity"="clinic"](around:{radius},{lat},{lon});
          node["amenity"="doctors"](around:{radius},{lat},{lon});
          node["amenity"="pharmacy"](around:{radius},{lat},{lon});
          way["amenity"="hospital"](around:{radius},{lat},{lon});
          way["amenity"="clinic"](around:{radius},{lat},{lon});
        );
        out center maxcount=15;
        """

        response = requests.post(
            overpass_url,
            data=overpass_query,
            timeout=30
        )

        if response.status_code != 200:
            return []

        data = response.json()
        hospitals = []

        for element in data.get("elements", []):
            tags = element.get("tags", {})
            name = tags.get("name", "Unnamed Medical Facility")

            # Get coordinates
            if element["type"] == "node":
                elem_lat = element.get("lat")
                elem_lon = element.get("lon")
            else:
                center = element.get("center", {})
                elem_lat = center.get("lat")
                elem_lon = center.get("lon")

            if not elem_lat or not elem_lon:
                continue

            # Calculate distance
            distance = calculate_distance(lat, lon, elem_lat, elem_lon)

            facility_type = tags.get("amenity", "medical").replace("_", " ").title()
            phone = tags.get("phone", tags.get("contact:phone", "Not available"))
            opening_hours = tags.get("opening_hours", "Not available")
            emergency = tags.get("emergency", "unknown")

            hospitals.append({
                "name": name,
                "type": facility_type,
                "lat": elem_lat,
                "lon": elem_lon,
                "distance_km": round(distance, 2),
                "phone": phone,
                "opening_hours": opening_hours,
                "emergency": emergency == "yes",
                "address": tags.get("addr:full",
                    f"{tags.get('addr:street', '')} {tags.get('addr:city', '')}".strip()
                    or "Address not available"
                )
            })

        # Sort by distance
        hospitals.sort(key=lambda x: x["distance_km"])
        return hospitals[:10]  # Return top 10 nearest

    except Exception as e:
        print(f"Hospital search error: {e}")
        return []


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in km (Haversine formula)"""
    from math import radians, sin, cos, sqrt, atan2

    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c