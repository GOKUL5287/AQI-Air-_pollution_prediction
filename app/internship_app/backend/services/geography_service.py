"""
TerraPulse Geography Service
Provides hierarchical geospatial coverage: Countries -> States/Provinces -> Cities -> Monitoring Stations.
Includes coastal classification and coordinates for seamless air and marine intelligence.
"""

from typing import List, Dict, Any, Optional

GLOBAL_COUNTRIES = [
    {
        "code": "US",
        "name": "United States",
        "continent": "North America",
        "lat": 37.0902,
        "lon": -95.7129,
        "is_coastal": True,
        "states": [
            {
                "code": "NY", "name": "New York", "lat": 40.7128, "lon": -74.0060,
                "cities": [
                    {"name": "New York City", "lat": 40.7128, "lon": -74.0060, "is_coastal": True, "station_id": "US-NYC-001", "station_name": "Manhattan - Central Park & Hudson Station"},
                    {"name": "Buffalo", "lat": 42.8864, "lon": -78.8784, "is_coastal": False, "station_id": "US-BUF-002", "station_name": "Buffalo Niagara Urban Station"}
                ]
            },
            {
                "code": "CA", "name": "California", "lat": 36.7783, "lon": -119.4179,
                "cities": [
                    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "is_coastal": True, "station_id": "US-LAX-001", "station_name": "Downtown LA - North Main St Station"},
                    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194, "is_coastal": True, "station_id": "US-SFO-002", "station_name": "SF Bay Area - Arkansas St Station"},
                    {"name": "San Diego", "lat": 32.7157, "lon": -117.1611, "is_coastal": True, "station_id": "US-SAN-003", "station_name": "San Diego Coastal Coastal Observatory"}
                ]
            },
            {
                "code": "WA", "name": "Washington", "lat": 47.7511, "lon": -120.7401,
                "cities": [
                    {"name": "Seattle", "lat": 47.6062, "lon": -122.3321, "is_coastal": True, "station_id": "US-SEA-001", "station_name": "Puget Sound - Beacon Hill Station"}
                ]
            }
        ]
    },
    {
        "code": "IN",
        "name": "India",
        "continent": "Asia",
        "lat": 20.5937,
        "lon": 78.9629,
        "is_coastal": True,
        "states": [
            {
                "code": "DL", "name": "Delhi", "lat": 28.7041, "lon": 77.1025,
                "cities": [
                    {"name": "New Delhi", "lat": 28.6139, "lon": 77.2090, "is_coastal": False, "station_id": "IN-DEL-001", "station_name": "Mandir Marg CPCB Monitoring Station"},
                    {"name": "Anand Vihar", "lat": 28.6508, "lon": 77.3152, "is_coastal": False, "station_id": "IN-DEL-002", "station_name": "Anand Vihar DPCC Continuous Observatory"}
                ]
            },
            {
                "code": "MH", "name": "Maharashtra", "lat": 19.7515, "lon": 75.7139,
                "cities": [
                    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "is_coastal": True, "station_id": "IN-BOM-001", "station_name": "Bandra Kurla Complex Air & Marine Lab"},
                    {"name": "Pune", "lat": 18.5204, "lon": 73.8567, "is_coastal": False, "station_id": "IN-PUN-002", "station_name": "Shivajinagar SAFAR Base"}
                ]
            },
            {
                "code": "KA", "name": "Karnataka", "lat": 15.3173, "lon": 75.7139,
                "cities": [
                    {"name": "Bengaluru", "lat": 12.9716, "lon": 77.5946, "is_coastal": False, "station_id": "IN-BLR-001", "station_name": "BTM Layout KSPCB Monitoring Station"}
                ]
            },
            {
                "code": "TN", "name": "Tamil Nadu", "lat": 11.1271, "lon": 78.6569,
                "cities": [
                    {"name": "Chennai", "lat": 13.0827, "lon": 80.2707, "is_coastal": True, "station_id": "IN-MAA-001", "station_name": "Marina Coastal Research & Air Lab"}
                ]
            }
        ]
    },
    {
        "code": "GB",
        "name": "United Kingdom",
        "continent": "Europe",
        "lat": 55.3781,
        "lon": -3.4360,
        "is_coastal": True,
        "states": [
            {
                "code": "ENG", "name": "England", "lat": 52.3555, "lon": -1.1743,
                "cities": [
                    {"name": "London", "lat": 51.5074, "lon": -0.1278, "is_coastal": True, "station_id": "UK-LON-001", "station_name": "London Bloomsbury Defra Superstation"},
                    {"name": "Southampton", "lat": 50.9097, "lon": -1.4044, "is_coastal": True, "station_id": "UK-SOU-002", "station_name": "Southampton Solent Marine Air Lab"}
                ]
            },
            {
                "code": "SCT", "name": "Scotland", "lat": 56.4907, "lon": -4.2026,
                "cities": [
                    {"name": "Edinburgh", "lat": 55.9533, "lon": -3.1883, "is_coastal": True, "station_id": "UK-EDI-001", "station_name": "Edinburgh St Leonards Urban Station"}
                ]
            }
        ]
    },
    {
        "code": "FR",
        "name": "France",
        "continent": "Europe",
        "lat": 46.2276,
        "lon": 2.2137,
        "is_coastal": True,
        "states": [
            {
                "code": "IDF", "name": "Île-de-France", "lat": 48.8499, "lon": 2.6370,
                "cities": [
                    {"name": "Paris", "lat": 48.8566, "lon": 2.3522, "is_coastal": False, "station_id": "FR-PAR-001", "station_name": "Airparif Paris Centre Observatoire"}
                ]
            },
            {
                "code": "PAC", "name": "Provence-Alpes-Côte d'Azur", "lat": 43.9352, "lon": 6.0679,
                "cities": [
                    {"name": "Marseille", "lat": 43.2965, "lon": 5.3698, "is_coastal": True, "station_id": "FR-MRS-001", "station_name": "AtmoSud Port de Marseille Littoral"}
                ]
            }
        ]
    },
    {
        "code": "DE",
        "name": "Germany",
        "continent": "Europe",
        "lat": 51.1657,
        "lon": 10.4515,
        "is_coastal": True,
        "states": [
            {
                "code": "BE", "name": "Berlin", "lat": 52.5200, "lon": 13.4050,
                "cities": [
                    {"name": "Berlin", "lat": 52.5200, "lon": 13.4050, "is_coastal": False, "station_id": "DE-BER-001", "station_name": "Berlin Mitte Umweltbundesamt"}
                ]
            },
            {
                "code": "HH", "name": "Hamburg", "lat": 53.5511, "lon": 9.9937,
                "cities": [
                    {"name": "Hamburg", "lat": 53.5511, "lon": 9.9937, "is_coastal": True, "station_id": "DE-HAM-001", "station_name": "Elbe Estuary Marine Air Monitor"}
                ]
            }
        ]
    },
    {
        "code": "JP",
        "name": "Japan",
        "continent": "Asia",
        "lat": 36.2048,
        "lon": 138.2529,
        "is_coastal": True,
        "states": [
            {
                "code": "TK", "name": "Tokyo", "lat": 35.6762, "lon": 139.6503,
                "cities": [
                    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "is_coastal": True, "station_id": "JP-TYO-001", "station_name": "Tokyo Metropolitan Ambient Air Center"}
                ]
            },
            {
                "code": "OS", "name": "Osaka", "lat": 34.6937, "lon": 135.5023,
                "cities": [
                    {"name": "Osaka", "lat": 34.6937, "lon": 135.5023, "is_coastal": True, "station_id": "JP-OSA-001", "station_name": "Osaka Bay Environmental Research Center"}
                ]
            }
        ]
    },
    {
        "code": "AU",
        "name": "Australia",
        "continent": "Oceania",
        "lat": -25.2744,
        "lon": 133.7751,
        "is_coastal": True,
        "states": [
            {
                "code": "NSW", "name": "New South Wales", "lat": -31.8402, "lon": 145.6128,
                "cities": [
                    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093, "is_coastal": True, "station_id": "AU-SYD-001", "station_name": "Sydney Harbour Coastal & Atmospheric Unit"}
                ]
            },
            {
                "code": "VIC", "name": "Victoria", "lat": -37.4713, "lon": 144.7852,
                "cities": [
                    {"name": "Melbourne", "lat": -37.8136, "lon": 144.9631, "is_coastal": True, "station_id": "AU-MEL-001", "station_name": "Port Phillip Bay Marine Air Station"}
                ]
            }
        ]
    },
    {
        "code": "BR",
        "name": "Brazil",
        "continent": "South America",
        "lat": -14.2350,
        "lon": -51.9253,
        "is_coastal": True,
        "states": [
            {
                "code": "SP", "name": "São Paulo", "lat": -23.5505, "lon": -46.6333,
                "cities": [
                    {"name": "São Paulo", "lat": -23.5505, "lon": -46.6333, "is_coastal": False, "station_id": "BR-SAO-001", "station_name": "CETESB Ibirapuera Air Station"}
                ]
            },
            {
                "code": "RJ", "name": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729,
                "cities": [
                    {"name": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729, "is_coastal": True, "station_id": "BR-RIO-001", "station_name": "Copacabana Atlantic Coastal Lab"}
                ]
            }
        ]
    },
    {
        "code": "EG",
        "name": "Egypt",
        "continent": "Africa",
        "lat": 26.8206,
        "lon": 30.8025,
        "is_coastal": True,
        "states": [
            {
                "code": "CAI", "name": "Cairo Governorate", "lat": 30.0444, "lon": 31.2357,
                "cities": [
                    {"name": "Cairo", "lat": 30.0444, "lon": 31.2357, "is_coastal": False, "station_id": "EG-CAI-001", "station_name": "Cairo Central EEAA Environmental Lab"}
                ]
            },
            {
                "code": "ALX", "name": "Alexandria Governorate", "lat": 31.2001, "lon": 29.9187,
                "cities": [
                    {"name": "Alexandria", "lat": 31.2001, "lon": 29.9187, "is_coastal": True, "station_id": "EG-ALX-001", "station_name": "Mediterranean Marine & Air Center"}
                ]
            }
        ]
    },
    {
        "code": "SG",
        "name": "Singapore",
        "continent": "Asia",
        "lat": 1.3521,
        "lon": 103.8198,
        "is_coastal": True,
        "states": [
            {
                "code": "SG", "name": "Singapore Central", "lat": 1.3521, "lon": 103.8198,
                "cities": [
                    {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "is_coastal": True, "station_id": "SG-SIN-001", "station_name": "NEA Straits Coastal & Ambient Lab"}
                ]
            }
        ]
    }
]

class GeographyService:
    @staticmethod
    def get_countries() -> List[Dict[str, Any]]:
        return [
            {
                "code": c["code"],
                "name": c["name"],
                "continent": c["continent"],
                "lat": c["lat"],
                "lon": c["lon"],
                "is_coastal": c["is_coastal"],
                "state_count": len(c.get("states", []))
            }
            for c in GLOBAL_COUNTRIES
        ]

    @staticmethod
    def get_states(country_code: str) -> List[Dict[str, Any]]:
        c_code = country_code.upper()
        for c in GLOBAL_COUNTRIES:
            if c["code"] == c_code:
                return [
                    {
                        "code": s["code"],
                        "name": s["name"],
                        "lat": s["lat"],
                        "lon": s["lon"],
                        "city_count": len(s.get("cities", []))
                    }
                    for s in c.get("states", [])
                ]
        return []

    @staticmethod
    def get_cities(country_code: str, state_code: Optional[str] = None) -> List[Dict[str, Any]]:
        c_code = country_code.upper()
        results = []
        for c in GLOBAL_COUNTRIES:
            if c["code"] == c_code:
                for s in c.get("states", []):
                    if state_code and s["code"].upper() != state_code.upper():
                        continue
                    for city in s.get("cities", []):
                        item = dict(city)
                        item["state_code"] = s["code"]
                        item["state_name"] = s["name"]
                        item["country_code"] = c["code"]
                        item["country_name"] = c["name"]
                        results.append(item)
        return results

    @staticmethod
    def search(query: str) -> List[Dict[str, Any]]:
        if not query or len(query.strip()) < 2:
            return []
        q = query.strip().lower()
        results = []

        for c in GLOBAL_COUNTRIES:
            # match country
            if q in c["name"].lower() or q == c["code"].lower():
                results.append({
                    "type": "country",
                    "title": c["name"],
                    "subtitle": f"Country in {c['continent']}",
                    "country_code": c["code"],
                    "lat": c["lat"],
                    "lon": c["lon"],
                    "is_coastal": c["is_coastal"]
                })

            for s in c.get("states", []):
                if q in s["name"].lower():
                    results.append({
                        "type": "state",
                        "title": s["name"],
                        "subtitle": f"State/Province in {c['name']}",
                        "country_code": c["code"],
                        "state_code": s["code"],
                        "lat": s["lat"],
                        "lon": s["lon"],
                        "is_coastal": c["is_coastal"]
                    })

                for city in s.get("cities", []):
                    if q in city["name"].lower() or q in city.get("station_name", "").lower():
                        results.append({
                            "type": "city",
                            "title": city["name"],
                            "subtitle": f"{s['name']}, {c['name']}",
                            "country_code": c["code"],
                            "state_code": s["code"],
                            "city_name": city["name"],
                            "station_name": city["station_name"],
                            "lat": city["lat"],
                            "lon": city["lon"],
                            "is_coastal": city["is_coastal"]
                        })

        return results[:15]

    @staticmethod
    def find_nearest_location(lat: float, lon: float) -> Optional[Dict[str, Any]]:
        best = None
        min_dist = float('inf')

        for c in GLOBAL_COUNTRIES:
            for s in c.get("states", []):
                for city in s.get("cities", []):
                    dist = (city["lat"] - lat)**2 + (city["lon"] - lon)**2
                    if dist < min_dist:
                        min_dist = dist
                        best = dict(city)
                        best["state_code"] = s["code"]
                        best["state_name"] = s["name"]
                        best["country_code"] = c["code"]
                        best["country_name"] = c["name"]
        return best
