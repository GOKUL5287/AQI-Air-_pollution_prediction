import unittest
from unittest.mock import patch

from app.internship_app.backend.app import AirQualityService, app


class LiveMapApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_live_status_reports_configuration_without_exposing_key(self):
        with patch.object(AirQualityService, "API_KEY", "test-key-not-for-response"):
            response = self.client.get("/api/air-quality/live-status")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["live_available"])
        self.assertNotIn("test-key-not-for-response", response.get_data(as_text=True))

    def test_current_reading_route_forwards_explicit_refresh(self):
        reading = {
            "status": "LIVE",
            "observed_measurements": {"pm25": 12.5},
            "provenance": "OBSERVED_WITH_ESTIMATES",
        }
        with patch.object(
            AirQualityService,
            "get_station_air_quality",
            return_value=reading,
        ) as get_reading:
            response = self.client.get(
                "/api/air-quality/current?lat=19.07&lon=72.87&station_id=123&refresh=1"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"], reading)
        get_reading.assert_called_once_with(19.07, 72.87, "123", force_refresh=True)

    def test_global_station_route_forwards_pagination(self):
        page = {
            "data": [{"station_id": "42", "country_code": "US"}],
            "total": 2500,
            "page_count": 1000,
            "page": 2,
            "limit": 1000,
        }
        with patch.object(
            AirQualityService,
            "get_openaq_global_locations",
            return_value=page,
        ) as get_locations:
            response = self.client.get("/api/regions/stations?page=2&limit=1000")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"], page["data"])
        get_locations.assert_called_once_with(page=2, limit=1000)

    def test_global_locations_include_sensor_types_and_country(self):
        payload = {
            "results": [{
                "id": 42,
                "name": "Central Park",
                "locality": "New York",
                "country": {"name": "United States", "code": "US"},
                "coordinates": {"latitude": 40.78, "longitude": -73.97},
                "sensors": [
                    {"parameter": {"name": "pm25"}},
                    {"parameter": {"name": "no2"}},
                ],
            }],
            "meta": {"found": ">1"},
        }
        with patch.object(AirQualityService, "API_KEY", "test-key"):
            with patch.object(
                AirQualityService, "_request_openaq", return_value=payload
            ) as request:
                result = AirQualityService.get_openaq_global_locations(page=3, limit=500)

        station = result["data"][0]
        self.assertEqual(station["country_code"], "US")
        self.assertEqual(station["parameters"], ["pm25", "no2"])
        self.assertEqual(result["page_count"], 1)
        request.assert_called_once_with(
            "locations", {"page": 3, "limit": 500, "isMobile": "false"}
        )


if __name__ == "__main__":
    unittest.main()
