from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import overpy
import geocoder
from typing import Tuple, List, Optional





class HospitalLocator:
    def __init__(self, default_radius: int = 5000):
        self.default_radius = default_radius
        self.geolocator = Nominatim(user_agent="my_hospital_search_app")
        self.api = overpy.Overpass()

    def get_current_location(self) -> Optional[Tuple[float, float]]:
        try:
            # Try multiple geocoding services
            g = geocoder.ip("me")
            if g.ok:
                return g.lat, g.lng

            return None
        except Exception as e:
            print(f"Error getting location: {e}")
            return None

    def search_hospitals(self, zipcode: Optional[str] = None) -> List[dict]:
        try:

            # First try using current location
            current_location = self.get_current_location()

            # If current location fails and no zipcode provided, raise error
            if not current_location and not zipcode:
                raise ValueError(
                    "Could not determine location. Please provide a valid zipcode."
                )

            # If current location fails or zipcode is provided, use zipcode
            if zipcode or not current_location:
                try:
                    g = self.geolocator.geocode(zipcode)
                    if g:
                        latitude, longitude = g.latitude, g.longitude
                    else:
                        raise ValueError(f"Invalid zipcode: {zipcode}")
                except Exception as e:
                    raise ValueError(f"Error processing zipcode: {str(e)}")
            else:
                # Use current location
                latitude, longitude = current_location

            radius = self.default_radius
            query = self._build_query(latitude, longitude, radius)
            result = self.api.query(query)
            final = self._process_results(result, (latitude, longitude))

            if not final:
                return [{"error": "No hospitals found in the specified area"}]
            return final

        except Exception as e:
            return [{"error": f"Error searching hospitals: {str(e)}"}]


    def _build_query(self, latitude: float, longitude: float, radius: int) -> str:
        return f"""(
            node["amenity"="hospital"](around:{radius},{latitude},{longitude});
            way["amenity"="hospital"](around:{radius},{latitude},{longitude});
            relation["amenity"="hospital"](around:{radius},{latitude},{longitude});
            );
            out center;
        """

    def _process_results(self, result, current_location: Tuple[float, float]) -> List[dict]:
        hospitals = []

        for node in result.nodes:
            hospital = self._create_hospital_dict(
                node.tags.get("name", "Unnamed Hospital"),
                (node.lat, node.lon),
                current_location,
            )
            hospitals.append(hospital)

        for way in result.ways:
            hospital = self._create_hospital_dict(
                way.tags.get("name", "Unnamed Hospital"),
                (way.center_lat, way.center_lon),
                current_location,
            )
            hospitals.append(hospital)

        return sorted(hospitals, key=lambda x: x["hospital_info"]["distance"])

    def _create_hospital_dict(
        self,
        name: str,
        location: Tuple[float, float],
        current_location: Tuple[float, float],
    ) -> dict:
        distance = self.calculate_distance(current_location, location)
        return {
            "hospital_info": {
                "name": name,
                "location": {"lat": location[0], "lng": location[1]},
                "distance": round(distance, 2),
            }
        }

    @staticmethod
    def calculate_distance(location1: Tuple[float, float], location2: Tuple[float, float]) -> float:
        return geodesic(location1, location2).meters

    def handle_hospital_query(self) -> str:
        try:
            locator = HospitalLocator()
            # Try to get current location first
            current_location = locator.get_current_location()

            if current_location:
                hospitals = locator.search_hospitals()
                if (
                    isinstance(hospitals, list)
                    and hospitals
                    and "error" not in hospitals[0]
                ):
                    response = "Here are the nearby hospitals:\n\n"
                    for hospital in hospitals:
                        info = hospital["hospital_info"]
                        distance_meters = info["distance"]
                        distance_km = distance_meters / 1000
                        response += f"* **{info['name']}** ({distance_km:.2f} km)\n"
                    return response
                else:
                    error_msg = hospitals[0].get("error", "Unknown error occurred")
                    return f"I apologize, but {error_msg.lower()}"
            else:
                return "I apologize, but I couldn't determine your current location. Could you please provide your zip code?"

        except Exception as e:
            return f"I apologize, but I encountered an error while searching for hospitals: {str(e)}"


locator = HospitalLocator()
hospitalList = locator.handle_hospital_query()

