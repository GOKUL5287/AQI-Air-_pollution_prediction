"""
TerraPulse Health & Environmental Advisory Service
Provides evidence-based, contextual health recommendations based on EPA / WHO air quality standards
and WHO recreational coastal water directives.
"""

from typing import Dict, Any, List

class HealthAdvisoryService:
    @staticmethod
    def get_air_health_advisory(aqi: float, dominant_pollutant: str = "PM2.5", temp_c: float = 22.0) -> Dict[str, Any]:
        """Contextual guidance based on verified AQI levels and dominant pollutant."""
        if aqi <= 50:
            status = "Good"
            severity = "LOW"
            general_text = "Air quality is considered satisfactory, and air pollution poses little or no risk."
            sensitive_text = "Ideal conditions for outdoor physical activities and ventilation."
            actions = [
                "Enjoy unrestricted outdoor sports and recreation.",
                "Natural ventilation of homes and workplaces is recommended.",
                "Zero respiratory protection required."
            ]
        elif aqi <= 100:
            status = "Moderate"
            severity = "MODERATE"
            general_text = "Air quality is acceptable; however, some pollutants may cause moderate health concern for a very small number of individuals."
            sensitive_text = "People with respiratory diseases (e.g. asthma) should consider limiting prolonged outdoor exertion."
            actions = [
                "Unusually sensitive individuals should monitor symptoms.",
                "Outdoor activities are generally safe for the public.",
                "Keep windows closed during peak traffic hours if near major thoroughfares."
            ]
        elif aqi <= 150:
            status = "Unhealthy for Sensitive Groups"
            severity = "HIGH_SENSITIVE"
            general_text = "Members of sensitive groups may experience adverse health effects. The general public is less likely to be affected."
            sensitive_text = "Children, the elderly, and individuals with cardiovascular or respiratory diseases must reduce prolonged outdoor exertion."
            actions = [
                f"Sensitive groups should wear certified N95/FFP2 respirators if {dominant_pollutant} is elevated outdoors.",
                "Limit intense cardiovascular exercise during high-pollution hours.",
                "Operate indoor air filtration systems (HEPA)."
            ]
        elif aqi <= 200:
            status = "Unhealthy"
            severity = "HIGH"
            general_text = "Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects."
            sensitive_text = "Avoid prolonged outdoor exertion. Sensitive groups should remain indoors."
            actions = [
                "Wear N95/KN95 respirators outdoors.",
                "Seal residential doors and windows; run HEPA air cleaners on high.",
                "Schools and athletic facilities should relocate sports indoors."
            ]
        elif aqi <= 300:
            status = "Very Unhealthy"
            severity = "VERY_HIGH"
            general_text = "Health alert: The risk of adverse health effects is increased for the entire population."
            sensitive_text = "Active children and adults, and people with respiratory disease, such as asthma, should avoid all outdoor exertion."
            actions = [
                "Strictly avoid outdoor exercise and non-essential travel.",
                "Wear sealed particulate respirators if stepping outside.",
                "Vulnerable individuals should keep quick-relief medications accessible."
            ]
        else:
            status = "Hazardous"
            severity = "EMERGENCY"
            general_text = "Health warnings of emergency conditions: The entire population is likely to be severely affected."
            sensitive_text = "Everyone must remain indoors with closed windows and active air purification."
            actions = [
                "Emergency health guidance: remain indoors in purified air environments.",
                "Avoid opening any external doors or windows.",
                "Seek medical attention immediately if experiencing acute shortness of breath or chest constriction."
            ]

        # Specific pollutant note
        pollutant_notes = {
            "PM2.5": "Fine particulates penetrate deep into lung alveoli and enter the bloodstream. HEPA filtration is most effective.",
            "PM10": "Inhalable coarse particles irritate upper airways, eyes, and mucous membranes.",
            "O3": "Ground-level ozone causes airway inflammation and chest tightness, especially during hot, sunny afternoons.",
            "NO2": "Nitrogen dioxide irritates lungs and lowers resistance to respiratory infections, particularly near vehicular exhaust.",
            "SO2": "Sulfur dioxide triggers bronchoconstriction in asthmatics within minutes of exposure.",
            "CO": "Carbon monoxide reduces oxygen delivery to organs; ensure indoor gas appliances are properly ventilated."
        }

        return {
            "aqi": aqi,
            "status": status,
            "severity": severity,
            "dominant_pollutant": dominant_pollutant,
            "general_population_guidance": general_text,
            "sensitive_groups_guidance": sensitive_text,
            "recommended_actions": actions,
            "pollutant_mechanism_note": pollutant_notes.get(dominant_pollutant, "Ambient pollutants affect cardiovascular and respiratory function."),
            "scientific_standard": "US EPA Air Quality Index Standard (40 CFR Part 58) & WHO 2021 Global Air Quality Guidelines",
            "provenance": "OFFICIAL_STANDARD_EVALUATION"
        }

    @staticmethod
    def get_marine_advisory(marine_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evidence-based guidance for coastal recreational safety and marine ecosystem state."""
        phys = marine_data.get("physical_oceanography", {})
        bio = marine_data.get("biogeochemical_indicators", {})

        wave_h = phys.get("wave_height_m", 1.0)
        sst = phys.get("sea_surface_temperature_c", 20.0)
        curr_vel = phys.get("current_velocity_kmh", 1.0)
        do = bio.get("dissolved_oxygen_mgl", 7.0)
        chl = bio.get("chlorophyll_a_mgm3", 0.5)

        hazards = []
        if wave_h > 2.5:
            hazards.append(f"High surf warning: significant wave height is {wave_h}m (danger of rip currents and shore break).")
        if curr_vel > 2.5:
            hazards.append(f"Strong coastal currents: velocity measured at {curr_vel} km/h.")
        if sst < 15.0:
            hazards.append(f"Cold water shock risk: sea temperature is {sst}°C. Wetsuit recommended.")
        if chl > 5.0:
            hazards.append(f"Potential phytoplankton / algal bloom detected: chlorophyll-a at {chl} mg/m³.")
        if do < 4.0:
            hazards.append(f"Hypoxic marine water condition: dissolved oxygen is critically low ({do} mg/L).")

        safe_swimming = len(hazards) == 0

        return {
            "recreational_safety": "SAFE" if safe_swimming else "CAUTION",
            "active_hazards": hazards,
            "wave_condition": "Calm" if wave_h < 1.0 else ("Moderate" if wave_h < 2.0 else "Rough"),
            "thermal_classification": "Warm / Tropical" if sst > 24 else ("Temperate" if sst > 17 else "Cold"),
            "water_clarity_secchi_m": bio.get("secchi_depth_m", 12.0),
            "scientific_source": "WHO Guidelines for Safe Recreational Water Environments & CMEMS Satellite Telemetry",
            "provenance": "OFFICIAL_STANDARD_EVALUATION"
        }
