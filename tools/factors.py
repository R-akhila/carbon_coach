
# Carbon emission factors
#
# Units:
# Travel: kg CO2e per passenger-km
# Electricity: kg CO2e per kWh
# Food: kg CO2e per serving
# Waste: kg CO2e per kg of waste
#
# IMPORTANT:
# These are prototype factors, not all verified official values.
# Replace provisional assumptions with documented local sources
# before presenting results as accurate real-world estimates.

EMISSION_FACTORS = {

    "Travel": {
        "Bus": {
            "factor": 0.08,
            "unit": "kg CO2e/passenger-km",
            "status": "Illustrative project example",
            "source": "Project brief example"
        },

        "Car": {
            "factor": 0.21,
            "unit": "kg CO2e/passenger-km",
            "status": "Provisional assumption",
            "source": "Demo assumption; verify before production"
        },

        "Motorcycle": {
            "factor": 0.10,
            "unit": "kg CO2e/passenger-km",
            "status": "Provisional assumption",
            "source": "Demo assumption; verify before production"
        },

        "Train": {
            "factor": 0.04,
            "unit": "kg CO2e/passenger-km",
            "status": "Provisional assumption",
            "source": "Demo assumption; verify before production"
        }
    },

    "Electricity": {
        "Electricity": {
            "factor": 0.716,
            "unit": "kg CO2e/kWh",
            "status": "Provisional grid factor",
            "source": "Older CEA India grid-factor reference; verify latest edition"
        }
    },

    "Food": {
        "Vegetarian": {
            "factor": 0.7,
            "unit": "kg CO2e/serving",
            "status": "Provisional assumption",
            "source": "Demo assumption; varies by meal"
        },

        "Non-vegetarian": {
            "factor": 2.5,
            "unit": "kg CO2e/serving",
            "status": "Provisional assumption",
            "source": "Demo assumption; varies by meal"
        }
    },

    "Waste": {
        "Plastic": {
            "factor": 2.5,
            "unit": "kg CO2e/kg",
            "status": "Provisional assumption",
            "source": "Demo assumption; depends on treatment"
        },

        "Paper": {
            "factor": 1.0,
            "unit": "kg CO2e/kg",
            "status": "Provisional assumption",
            "source": "Demo assumption; depends on recycling"
        },

        "Organic": {
            "factor": 0.5,
            "unit": "kg CO2e/kg",
            "status": "Provisional assumption",
            "source": "Demo assumption; depends on disposal"
        }
    }
}
