# =============================================================================
# SPEQTR REPAIR COST LOOKUP TABLE
# Sources: Angi, HomeAdvisor, HomeStars Canada, Redfin, 2025 cost guides
# USD = Illinois/Chicagoland rates | CAD = Alberta/Calgary rates
# Update annually. Last updated: 2025.
# =============================================================================

# Structure: category_key -> { display, usd_low, usd_high, cad_low, cad_high, trade, note }
# All values in whole dollars. note = shown to user as context.

COST_TABLE = {

    # -------------------------------------------------------------------------
    # ELECTRICAL
    # -------------------------------------------------------------------------
    "ELEC_GFCI_OUTLETS": {
        "display": "GFCI outlet installation",
        "usd_low": 150, "usd_high": 300,
        "cad_low": 200, "cad_high": 400,
        "trade": "Electrician",
        "note": "Per 2-4 outlets"
    },
    "ELEC_DOUBLE_TAPPED_BREAKER": {
        "display": "Double-tapped breaker repair",
        "usd_low": 150, "usd_high": 250,
        "cad_low": 200, "cad_high": 350,
        "trade": "Electrician",
        "note": "Per breaker"
    },
    "ELEC_PANEL_UPGRADE": {
        "display": "Electrical panel upgrade (100→200 amp)",
        "usd_low": 1500, "usd_high": 3000,
        "cad_low": 2000, "cad_high": 4500,
        "trade": "Electrician",
        "note": "Includes permit"
    },
    "ELEC_PANEL_REPLACE": {
        "display": "Electrical panel replacement",
        "usd_low": 1200, "usd_high": 2500,
        "cad_low": 1500, "cad_high": 3500,
        "trade": "Electrician",
        "note": "Same amperage replacement"
    },
    "ELEC_REWIRE_FULL": {
        "display": "Full home rewiring",
        "usd_low": 8000, "usd_high": 20000,
        "cad_low": 10000, "cad_high": 25000,
        "trade": "Electrician",
        "note": "Varies significantly by home size"
    },
    "ELEC_ALUMINUM_WIRING": {
        "display": "Aluminum wiring remediation",
        "usd_low": 5000, "usd_high": 15000,
        "cad_low": 6000, "cad_high": 18000,
        "trade": "Electrician",
        "note": "Full remediation or pigtailing"
    },
    "ELEC_KNOB_TUBE": {
        "display": "Knob-and-tube wiring replacement",
        "usd_low": 6000, "usd_high": 15000,
        "cad_low": 7000, "cad_high": 18000,
        "trade": "Electrician",
        "note": "Partial or full depending on extent"
    },
    "ELEC_OUTLETS_MINOR": {
        "display": "Outlet/switch repairs (minor)",
        "usd_low": 75, "usd_high": 250,
        "cad_low": 100, "cad_high": 300,
        "trade": "Electrician",
        "note": "Loose, ungrounded, or reverse polarity outlets"
    },
    "ELEC_SMOKE_DETECTORS": {
        "display": "Smoke/CO detector installation",
        "usd_low": 50, "usd_high": 200,
        "cad_low": 75, "cad_high": 250,
        "trade": "Electrician or DIY",
        "note": "Per unit installed"
    },
    "ELEC_AFCI_BREAKERS": {
        "display": "AFCI breaker installation",
        "usd_low": 200, "usd_high": 600,
        "cad_low": 250, "cad_high": 750,
        "trade": "Electrician",
        "note": "Per circuit"
    },

    # -------------------------------------------------------------------------
    # PLUMBING
    # -------------------------------------------------------------------------
    "PLUMB_FAUCET_REPAIR": {
        "display": "Faucet repair or replacement",
        "usd_low": 150, "usd_high": 400,
        "cad_low": 350, "cad_high": 550,
        "trade": "Plumber",
        "note": "Includes labour and basic fixture"
    },
    "PLUMB_TOILET_REPAIR": {
        "display": "Toilet repair or replacement",
        "usd_low": 150, "usd_high": 500,
        "cad_low": 200, "cad_high": 600,
        "trade": "Plumber",
        "note": "Standard toilet replacement"
    },
    "PLUMB_DRAIN_UNCLOG": {
        "display": "Drain clearing/unclogging",
        "usd_low": 150, "usd_high": 400,
        "cad_low": 300, "cad_high": 450,
        "trade": "Plumber",
        "note": "Standard drain snake or hydro-jet"
    },
    "PLUMB_WATER_HEATER": {
        "display": "Water heater replacement (40-50 gal gas)",
        "usd_low": 900, "usd_high": 3000,
        "cad_low": 3500, "cad_high": 6000,
        "trade": "Plumber",
        "note": "Includes removal of old unit"
    },
    "PLUMB_WATER_HEATER_TANKLESS": {
        "display": "Tankless water heater installation",
        "usd_low": 2500, "usd_high": 5000,
        "cad_low": 3500, "cad_high": 7000,
        "trade": "Plumber",
        "note": "Gas or electric"
    },
    "PLUMB_LEAK_MINOR": {
        "display": "Plumbing leak repair (minor)",
        "usd_low": 150, "usd_high": 600,
        "cad_low": 400, "cad_high": 900,
        "trade": "Plumber",
        "note": "Visible pipe or fixture leak"
    },
    "PLUMB_SEWER_SCOPE": {
        "display": "Sewer scope/camera inspection",
        "usd_low": 300, "usd_high": 500,
        "cad_low": 400, "cad_high": 650,
        "trade": "Plumber",
        "note": "Diagnostic only — repair costs additional"
    },
    "PLUMB_SEWER_REPAIR": {
        "display": "Sewer line repair",
        "usd_low": 1500, "usd_high": 6000,
        "cad_low": 2000, "cad_high": 8000,
        "trade": "Plumber",
        "note": "Partial repair; full replacement $5,000–$15,000"
    },
    "PLUMB_REPIPE": {
        "display": "Full home repipe (galvanized/polybutylene)",
        "usd_low": 5000, "usd_high": 15000,
        "cad_low": 6000, "cad_high": 18000,
        "trade": "Plumber",
        "note": "Varies significantly by home size"
    },
    "PLUMB_WATER_PRESSURE": {
        "display": "Water pressure issue repair",
        "usd_low": 150, "usd_high": 500,
        "cad_low": 200, "cad_high": 600,
        "trade": "Plumber",
        "note": "Pressure regulator or valve issue"
    },
    "PLUMB_SUMP_PUMP": {
        "display": "Sump pump replacement",
        "usd_low": 500, "usd_high": 1200,
        "cad_low": 650, "cad_high": 1500,
        "trade": "Plumber",
        "note": "Includes installation"
    },
    "PLUMB_BACKFLOW": {
        "display": "Backflow preventer installation",
        "usd_low": 300, "usd_high": 800,
        "cad_low": 400, "cad_high": 900,
        "trade": "Plumber",
        "note": ""
    },

    # -------------------------------------------------------------------------
    # HVAC
    # -------------------------------------------------------------------------
    "HVAC_SERVICE_TUNE": {
        "display": "HVAC service/tune-up",
        "usd_low": 80, "usd_high": 200,
        "cad_low": 120, "cad_high": 300,
        "trade": "HVAC Technician",
        "note": "Annual maintenance service"
    },
    "HVAC_FURNACE_REPLACE": {
        "display": "Furnace replacement",
        "usd_low": 2500, "usd_high": 6000,
        "cad_low": 3500, "cad_high": 7000,
        "trade": "HVAC Technician",
        "note": "Gas forced air; high-efficiency units at higher end"
    },
    "HVAC_AC_REPLACE": {
        "display": "Central AC unit replacement",
        "usd_low": 3000, "usd_high": 7000,
        "cad_low": 4000, "cad_high": 8500,
        "trade": "HVAC Technician",
        "note": "Condenser only; full system replacement higher"
    },
    "HVAC_FULL_SYSTEM": {
        "display": "Full HVAC system replacement (furnace + AC)",
        "usd_low": 7000, "usd_high": 16000,
        "cad_low": 9000, "cad_high": 20000,
        "trade": "HVAC Technician",
        "note": "Includes ductwork modifications if needed"
    },
    "HVAC_HEAT_PUMP": {
        "display": "Heat pump installation",
        "usd_low": 4000, "usd_high": 10000,
        "cad_low": 3500, "cad_high": 7500,
        "trade": "HVAC Technician",
        "note": "Air source heat pump"
    },
    "HVAC_DUCT_REPAIR": {
        "display": "Ductwork repair",
        "usd_low": 300, "usd_high": 1000,
        "cad_low": 400, "cad_high": 1200,
        "trade": "HVAC Technician",
        "note": "Sealing, insulating, or patching ducts"
    },
    "HVAC_FILTER_MINOR": {
        "display": "Filter replacement / minor HVAC repair",
        "usd_low": 50, "usd_high": 200,
        "cad_low": 75, "cad_high": 250,
        "trade": "HVAC Technician or DIY",
        "note": "Filters, belts, minor components"
    },
    "HVAC_HUMIDIFIER": {
        "display": "Whole-home humidifier installation",
        "usd_low": 400, "usd_high": 900,
        "cad_low": 500, "cad_high": 1100,
        "trade": "HVAC Technician",
        "note": ""
    },

    # -------------------------------------------------------------------------
    # ROOFING
    # -------------------------------------------------------------------------
    "ROOF_MINOR_REPAIR": {
        "display": "Roof repair (minor — shingles, flashing, boots)",
        "usd_low": 300, "usd_high": 1500,
        "cad_low": 400, "cad_high": 1800,
        "trade": "Roofer",
        "note": "Spot repairs, isolated areas"
    },
    "ROOF_MODERATE_REPAIR": {
        "display": "Roof repair (moderate — multiple areas)",
        "usd_low": 1500, "usd_high": 4000,
        "cad_low": 1800, "cad_high": 5000,
        "trade": "Roofer",
        "note": "Larger sections or multiple issues"
    },
    "ROOF_REPLACEMENT": {
        "display": "Full roof replacement (asphalt shingle)",
        "usd_low": 6500, "usd_high": 12000,
        "cad_low": 8000, "cad_high": 15000,
        "trade": "Roofer",
        "note": "Per 1,500–2,000 sq ft; larger homes higher"
    },
    "ROOF_CHIMNEY_FLASHING": {
        "display": "Chimney flashing repair/replacement",
        "usd_low": 400, "usd_high": 1600,
        "cad_low": 500, "cad_high": 2000,
        "trade": "Roofer or Mason",
        "note": ""
    },
    "ROOF_GUTTERS_CLEAN": {
        "display": "Gutter cleaning",
        "usd_low": 120, "usd_high": 250,
        "cad_low": 150, "cad_high": 350,
        "trade": "General Contractor or DIY",
        "note": "Per service"
    },
    "ROOF_GUTTERS_REPLACE": {
        "display": "Gutter replacement",
        "usd_low": 800, "usd_high": 2500,
        "cad_low": 1000, "cad_high": 3000,
        "trade": "General Contractor",
        "note": "Full perimeter; seamless aluminum"
    },
    "ROOF_SOFFIT_FASCIA": {
        "display": "Soffit and fascia repair/replacement",
        "usd_low": 500, "usd_high": 2500,
        "cad_low": 600, "cad_high": 3000,
        "trade": "General Contractor",
        "note": "Partial repair; full replacement higher"
    },
    "ROOF_SKYLIGHT": {
        "display": "Skylight repair or replacement",
        "usd_low": 500, "usd_high": 2800,
        "cad_low": 600, "cad_high": 3500,
        "trade": "Roofer",
        "note": ""
    },

    # -------------------------------------------------------------------------
    # FOUNDATION & STRUCTURAL
    # -------------------------------------------------------------------------
    "FOUND_CRACK_MINOR": {
        "display": "Foundation crack repair (minor hairline cracks)",
        "usd_low": 500, "usd_high": 2500,
        "cad_low": 600, "cad_high": 3000,
        "trade": "Foundation Specialist",
        "note": "Injection or patching; structural evaluation recommended"
    },
    "FOUND_CRACK_MAJOR": {
        "display": "Foundation repair (structural/major cracks)",
        "usd_low": 2200, "usd_high": 8100,
        "cad_low": 3000, "cad_high": 10000,
        "trade": "Foundation Specialist / Structural Engineer",
        "note": "Underpinning or full repair can exceed this range"
    },
    "FOUND_WATERPROOFING": {
        "display": "Basement waterproofing",
        "usd_low": 3000, "usd_high": 10000,
        "cad_low": 4000, "cad_high": 12000,
        "trade": "Waterproofing Specialist",
        "note": "Interior or exterior system; varies significantly"
    },
    "FOUND_CRAWLSPACE": {
        "display": "Crawlspace repair/encapsulation",
        "usd_low": 2000, "usd_high": 8000,
        "cad_low": 2500, "cad_high": 10000,
        "trade": "Foundation Specialist",
        "note": "Moisture barrier, venting, minor structural"
    },

    # -------------------------------------------------------------------------
    # WINDOWS & DOORS
    # -------------------------------------------------------------------------
    "WIN_SEAL_REPAIR": {
        "display": "Window seal repair (fogged glass)",
        "usd_low": 150, "usd_high": 400,
        "cad_low": 200, "cad_high": 500,
        "trade": "Window Contractor",
        "note": "Per window; glass unit replacement"
    },
    "WIN_SINGLE_REPLACE": {
        "display": "Single window replacement",
        "usd_low": 350, "usd_high": 850,
        "cad_low": 450, "cad_high": 1100,
        "trade": "Window Contractor",
        "note": "Standard double-hung vinyl; custom sizes higher"
    },
    "WIN_FULL_REPLACE": {
        "display": "Full home window replacement",
        "usd_low": 8000, "usd_high": 24000,
        "cad_low": 10000, "cad_high": 30000,
        "trade": "Window Contractor",
        "note": "Depends on number and size of windows"
    },
    "DOOR_REPAIR": {
        "display": "Door repair or replacement",
        "usd_low": 200, "usd_high": 800,
        "cad_low": 250, "cad_high": 1000,
        "trade": "Carpenter / General Contractor",
        "note": "Exterior doors higher; includes hardware"
    },

    # -------------------------------------------------------------------------
    # MOLD, WATER & ENVIRONMENTAL
    # -------------------------------------------------------------------------
    "MOLD_MINOR": {
        "display": "Mold remediation (minor/isolated)",
        "usd_low": 500, "usd_high": 3000,
        "cad_low": 700, "cad_high": 4000,
        "trade": "Mold Remediation Specialist",
        "note": "Small area; limited spread"
    },
    "MOLD_MAJOR": {
        "display": "Mold remediation (major/widespread)",
        "usd_low": 3000, "usd_high": 15000,
        "cad_low": 4000, "cad_high": 18000,
        "trade": "Mold Remediation Specialist",
        "note": "Involves structural materials or large area"
    },
    "RADON_MITIGATION": {
        "display": "Radon mitigation system",
        "usd_low": 1750, "usd_high": 5000,
        "cad_low": 2000, "cad_high": 6000,
        "trade": "Radon Mitigation Specialist",
        "note": "Cost may be higher depending on foundation type, soil conditions, and number of entry points. Post-mitigation testing recommended."
    },
    "WATER_DAMAGE_REPAIR": {
        "display": "Water damage repair",
        "usd_low": 1500, "usd_high": 9000,
        "cad_low": 2000, "cad_high": 11000,
        "trade": "Water Damage Restoration",
        "note": "Highly variable based on extent and affected materials"
    },

    # -------------------------------------------------------------------------
    # INSULATION & ATTIC
    # -------------------------------------------------------------------------
    "INSUL_ATTIC": {
        "display": "Attic insulation (blown-in or batt)",
        "usd_low": 1500, "usd_high": 4000,
        "cad_low": 1800, "cad_high": 5000,
        "trade": "Insulation Contractor",
        "note": "Per 1,000–1,500 sq ft attic"
    },
    "INSUL_CRAWLSPACE": {
        "display": "Crawlspace insulation",
        "usd_low": 1000, "usd_high": 3500,
        "cad_low": 1200, "cad_high": 4500,
        "trade": "Insulation Contractor",
        "note": ""
    },

    # -------------------------------------------------------------------------
    # DECK & EXTERIOR
    # -------------------------------------------------------------------------
    "DECK_REPAIR": {
        "display": "Deck repair",
        "usd_low": 500, "usd_high": 2500,
        "cad_low": 600, "cad_high": 3000,
        "trade": "General Contractor / Carpenter",
        "note": "Board replacement, railings, ledger board"
    },
    "DECK_REPLACE": {
        "display": "Deck replacement",
        "usd_low": 5000, "usd_high": 15000,
        "cad_low": 6000, "cad_high": 18000,
        "trade": "General Contractor",
        "note": "Pressure-treated lumber; composite decking higher"
    },
    "SIDING_REPAIR": {
        "display": "Siding repair",
        "usd_low": 300, "usd_high": 1500,
        "cad_low": 400, "cad_high": 2000,
        "trade": "General Contractor",
        "note": "Partial repair; full replacement significantly higher"
    },
    "SIDING_REPLACE": {
        "display": "Full siding replacement",
        "usd_low": 6000, "usd_high": 18000,
        "cad_low": 7000, "cad_high": 22000,
        "trade": "General Contractor",
        "note": "Vinyl; fiber cement or wood higher"
    },
    "DRIVEWAY_REPAIR": {
        "display": "Driveway repair",
        "usd_low": 300, "usd_high": 2000,
        "cad_low": 400, "cad_high": 2500,
        "trade": "Concrete / Paving Contractor",
        "note": "Crack sealing to resurfacing"
    },

    # -------------------------------------------------------------------------
    # CHIMNEY & FIREPLACE
    # -------------------------------------------------------------------------
    "CHIMNEY_CLEAN": {
        "display": "Chimney cleaning and inspection",
        "usd_low": 150, "usd_high": 400,
        "cad_low": 200, "cad_high": 500,
        "trade": "Chimney Specialist",
        "note": "Annual sweep and Level 1 inspection"
    },
    "CHIMNEY_REPAIR": {
        "display": "Chimney repair (liner, crown, mortar)",
        "usd_low": 500, "usd_high": 3000,
        "cad_low": 600, "cad_high": 3500,
        "trade": "Chimney Specialist / Mason",
        "note": "Varies by type and extent of damage"
    },
    "CHIMNEY_REBUILD": {
        "display": "Chimney partial or full rebuild",
        "usd_low": 3000, "usd_high": 10000,
        "cad_low": 4000, "cad_high": 12000,
        "trade": "Mason",
        "note": ""
    },

    # -------------------------------------------------------------------------
    # GARAGE
    # -------------------------------------------------------------------------
    "GARAGE_DOOR": {
        "display": "Garage door repair or replacement",
        "usd_low": 200, "usd_high": 2000,
        "cad_low": 250, "cad_high": 2500,
        "trade": "Garage Door Specialist",
        "note": "Springs/cables at low end; full replacement at high end"
    },
    "GARAGE_OPENER": {
        "display": "Garage door opener replacement",
        "usd_low": 300, "usd_high": 700,
        "cad_low": 350, "cad_high": 900,
        "trade": "Garage Door Specialist",
        "note": "Includes installation"
    },
}


def get_cost(category_key, currency="USD"):
    """
    Returns (low, high, display_name, trade, note) for a given category.
    currency: 'USD' or 'CAD'
    Returns None if category not found.
    """
    item = COST_TABLE.get(category_key)
    if not item:
        return None

    if currency == "CAD":
        return {
            "low": item["cad_low"],
            "high": item["cad_high"],
            "display": item["display"],
            "trade": item["trade"],
            "note": item["note"],
            "currency": "CAD",
            "source": "lookup_table"
        }
    else:
        return {
            "low": item["usd_low"],
            "high": item["usd_high"],
            "display": item["display"],
            "trade": item["trade"],
            "note": item["note"],
            "currency": "USD",
            "source": "lookup_table"
        }


def format_cost_range(low, high, currency="USD"):
    """Format cost range as string e.g. '$1,500 - $3,000'"""
    symbol = "$"
    return f"{symbol}{low:,} - {symbol}{high:,}"


def get_all_categories():
    """Return list of all category keys — used in AI prompt."""
    return list(COST_TABLE.keys())
# =============================================================================
# EXTENDED LOOKUP TABLE — added to fix ai_estimate fallthrough
# All 59 keys referenced in alias map but missing from COST_TABLE
# USD = Illinois/Chicagoland | CAD = Alberta/Calgary
# =============================================================================

_EXTENDED = {

    # EXTERIOR
    "EXT_VEGETATION": {"display": "Vegetation / overgrowth removal from structure","usd_low": 100,"usd_high": 400,"cad_low": 150,"cad_high": 500,"trade": "Landscaper / General Contractor","note": "Trimming and removal of shrubs or vines contacting structure"},
    "EXT_VENT_COVERS": {"display": "Damaged vent cover replacement","usd_low": 75,"usd_high": 300,"cad_low": 100,"cad_high": 400,"trade": "Handyman / General Contractor","note": "Per vent cover; includes labour"},
    "EXT_GRADE_DRAINAGE": {"display": "Grading / drainage correction","usd_low": 300,"usd_high": 2000,"cad_low": 400,"cad_high": 2500,"trade": "Landscaper / General Contractor","note": "Localized regrading; major drainage work higher"},
    "EXT_FOUNDATION_PAINT": {"display": "Foundation staining / paint depletion repair","usd_low": 150,"usd_high": 600,"cad_low": 200,"cad_high": 750,"trade": "General Contractor / Painter","note": "Surface treatment; underlying water issue may add cost"},
    "EXT_STUCCO_CRACK": {"display": "Stucco crack repair (localized)","usd_low": 250,"usd_high": 1200,"cad_low": 300,"cad_high": 1500,"trade": "Stucco / General Contractor","note": "Patch and finish; EIFS systems higher"},
    "EXT_EIFS_MOISTURE": {"display": "EIFS stucco moisture intrusion repair","usd_low": 2000,"usd_high": 12000,"cad_low": 2500,"cad_high": 15000,"trade": "Building Envelope Specialist","note": "Highly variable; full envelope remediation at high end"},
    "EXT_WOODPECKER": {"display": "Woodpecker damage repair (EIFS / siding)","usd_low": 500,"usd_high": 4000,"cad_low": 600,"cad_high": 5000,"trade": "Building Envelope Specialist / General Contractor","note": "Patch and seal; full envelope assessment recommended"},
    "EXT_HANDRAIL": {"display": "Handrail / guardrail installation or repair","usd_low": 300,"usd_high": 1200,"cad_low": 400,"cad_high": 1500,"trade": "General Contractor / Carpenter","note": "Per run of stairs or landing"},
    "EXT_DRIVEWAY_LEVEL": {"display": "Driveway slab leveling / foam jacking","usd_low": 400,"usd_high": 2500,"cad_low": 500,"cad_high": 3000,"trade": "Concrete Contractor","note": "Foam injection or mudjacking; full replacement higher"},
    "EXT_RETAINING_WALL": {"display": "Retaining wall repair","usd_low": 500,"usd_high": 5000,"cad_low": 600,"cad_high": 6000,"trade": "General Contractor / Structural Engineer","note": "Localized repair; full rebuild significantly higher"},
    "EXT_MORTAR_JOINTS": {"display": "Mortar joint / tuckpointing repair","usd_low": 400,"usd_high": 2500,"cad_low": 500,"cad_high": 3000,"trade": "Mason","note": "Per section; full repointing of facade higher"},

    # ROOF
    "ROOF_BOOTS_SEALANT": {"display": "Roof boots / sealants replacement","usd_low": 300,"usd_high": 1200,"cad_low": 400,"cad_high": 1800,"trade": "Roofer","note": "Per boot or localized sealant; full roof inspection recommended"},
    "ROOF_GUTTER_CLEAN": {"display": "Gutter cleaning and debris removal","usd_low": 100,"usd_high": 350,"cad_low": 150,"cad_high": 450,"trade": "Handyman / Gutter Specialist","note": "Full gutter flush and downspout check"},
    "ROOF_PENETRATION_FLAT": {"display": "Flat roof penetration sealing","usd_low": 200,"usd_high": 800,"cad_low": 250,"cad_high": 1000,"trade": "Roofer","note": "Per penetration; includes sealant and flashing"},

    # DECK
    "DECK_SEALANT": {"display": "Deck sealant / stain reapplication","usd_low": 400,"usd_high": 2000,"cad_low": 500,"cad_high": 2500,"trade": "Deck Contractor / Handyman","note": "Cleaning, prep and reseal; size dependent"},

    # WINDOWS
    "WIN_CRANK_HARDWARE": {"display": "Window crank / hardware repair","usd_low": 75,"usd_high": 300,"cad_low": 100,"cad_high": 400,"trade": "Window Technician / Handyman","note": "Per window; hardware replacement"},
    "WIN_CRACKED_GLASS": {"display": "Cracked or broken window glass replacement","usd_low": 150,"usd_high": 500,"cad_low": 200,"cad_high": 650,"trade": "Window Contractor","note": "IGU replacement; frame damage additional"},

    # FOUNDATION
    "FOUND_CRACK_MINOR": {"display": "Foundation crack repair (minor / hairline)","usd_low": 300,"usd_high": 1500,"cad_low": 400,"cad_high": 2000,"trade": "Foundation Specialist","note": "Epoxy or polyurethane injection; structural cracks higher"},
    "FOUND_CRACK_MAJOR": {"display": "Foundation crack repair (major / structural)","usd_low": 3000,"usd_high": 12000,"cad_low": 4000,"cad_high": 15000,"trade": "Structural Engineer / Foundation Specialist","note": "Requires engineering assessment; underpinning at high end"},
    "FOUND_WATERPROOF_INT": {"display": "Basement waterproofing (interior)","usd_low": 3000,"usd_high": 10000,"cad_low": 4000,"cad_high": 12000,"trade": "Waterproofing Contractor","note": "Interior drain tile and sump system"},
    "FOUND_WATERPROOF_EXT": {"display": "Basement waterproofing (exterior)","usd_low": 5000,"usd_high": 18000,"cad_low": 6000,"cad_high": 22000,"trade": "Waterproofing Contractor","note": "Excavation required; highly variable by foundation perimeter"},
    "FOUND_WATER_INTRUSION": {"display": "Foundation water intrusion repair","usd_low": 1000,"usd_high": 8000,"cad_low": 1200,"cad_high": 10000,"trade": "Foundation / Waterproofing Specialist","note": "Scope varies widely; full assessment required"},

    # STRUCTURAL
    "STRUCT_ENGINEER_INSPECT": {"display": "Structural engineer inspection / assessment","usd_low": 400,"usd_high": 1200,"cad_low": 500,"cad_high": 1500,"trade": "Structural Engineer","note": "Inspection and written report; remediation costs additional"},

    # ELECTRICAL (extended)
    "ELEC_OUTLET_REPAIR": {"display": "Outlet repair or replacement","usd_low": 75,"usd_high": 200,"cad_low": 100,"cad_high": 250,"trade": "Electrician","note": "Per outlet; tamper-resistant or GFCI higher"},
    "ELEC_REVERSE_POLARITY": {"display": "Reverse polarity outlet correction","usd_low": 75,"usd_high": 200,"cad_low": 100,"cad_high": 250,"trade": "Electrician","note": "Per outlet; simple wire swap"},
    "ELEC_LIGHT_SWITCH": {"display": "Light switch repair or replacement","usd_low": 75,"usd_high": 150,"cad_low": 100,"cad_high": 200,"trade": "Electrician","note": "Per switch; dimmer or smart switch higher"},
    "ELEC_LIGHT_FIXTURE": {"display": "Light fixture repair or replacement","usd_low": 100,"usd_high": 350,"cad_low": 125,"cad_high": 450,"trade": "Electrician","note": "Labour only; fixture cost additional"},
    "ELEC_BREAKER_REPLACE": {"display": "Circuit breaker replacement","usd_low": 150,"usd_high": 400,"cad_low": 200,"cad_high": 500,"trade": "Electrician","note": "Per breaker; panel condition may affect cost"},
    "ELEC_DEDICATED_CIRCUIT": {"display": "Dedicated circuit installation","usd_low": 300,"usd_high": 800,"cad_low": 400,"cad_high": 1000,"trade": "Electrician","note": "New circuit from panel; includes breaker"},

    # PLUMBING (extended)
    "PLUMB_SEWER_CAP": {"display": "Sewer line penetration capping","usd_low": 200,"usd_high": 600,"cad_low": 250,"cad_high": 750,"trade": "Plumber","note": "Sealing open penetration; scope inspection recommended"},
    "PLUMB_WATER_HEATER_VENT": {"display": "Water heater vent correction","usd_low": 200,"usd_high": 700,"cad_low": 250,"cad_high": 900,"trade": "Plumber / HVAC Technician","note": "Vent pipe correction or extension"},
    "PLUMB_SEDIMENT_TRAP": {"display": "Sediment trap installation","usd_low": 150,"usd_high": 400,"cad_low": 200,"cad_high": 500,"trade": "Plumber","note": "Gas line sediment trap; code requirement"},
    "PLUMB_PIPE_LEAK_ACCESSIBLE": {"display": "Pipe leak repair (accessible)","usd_low": 150,"usd_high": 500,"cad_low": 200,"cad_high": 650,"trade": "Plumber","note": "Exposed pipe; fitting or section replacement"},
    "PLUMB_PIPE_LEAK_WALL": {"display": "Pipe leak repair (in wall / concealed)","usd_low": 500,"usd_high": 2500,"cad_low": 650,"cad_high": 3000,"trade": "Plumber","note": "Includes wall opening, repair and patch"},
    "PLUMB_DRAIN_REPAIR": {"display": "Drain pipe repair","usd_low": 200,"usd_high": 800,"cad_low": 250,"cad_high": 1000,"trade": "Plumber","note": "Localized drain repair or replacement"},
    "PLUMB_GARBAGE_DISPOSAL": {"display": "Garbage disposal replacement","usd_low": 200,"usd_high": 500,"cad_low": 250,"cad_high": 650,"trade": "Plumber","note": "Standard unit; includes installation"},
    "PLUMB_BATHTUB_REPAIR": {"display": "Bathtub resurfacing or chip repair","usd_low": 200,"usd_high": 600,"cad_low": 250,"cad_high": 750,"trade": "Plumber / Tile Specialist","note": "Reglazing or repair; full replacement higher"},

    # HVAC (extended)
    "HVAC_AC_LINE_INSULATION": {"display": "AC line set insulation replacement","usd_low": 100,"usd_high": 350,"cad_low": 150,"cad_high": 450,"trade": "HVAC Technician","note": "Insulate refrigerant lines; per linear section"},
    "HVAC_ATTIC_PLATFORM": {"display": "Attic service platform installation","usd_low": 300,"usd_high": 900,"cad_low": 400,"cad_high": 1100,"trade": "General Contractor / HVAC Technician","note": "Catwalk or platform for equipment access"},

    # APPLIANCES
    "APPL_DRYER_VENT": {"display": "Dryer vent cleaning or rerouting","usd_low": 100,"usd_high": 400,"cad_low": 150,"cad_high": 500,"trade": "HVAC Technician / Handyman","note": "Cleaning at low end; rerouting to exterior higher"},
    "APPL_RANGE_HOOD_VENT": {"display": "Range hood vent correction","usd_low": 150,"usd_high": 600,"cad_low": 200,"cad_high": 750,"trade": "General Contractor / HVAC Technician","note": "Proper exterior termination required"},

    # INTERIOR
    "INT_WALL_CRACK": {"display": "Drywall / wall crack repair","usd_low": 150,"usd_high": 800,"cad_low": 200,"cad_high": 1000,"trade": "Drywall Contractor / Handyman","note": "Patch, tape and finish; settlement cracks may recur"},
    "INT_DRYWALL_PATCH": {"display": "Drywall patch (small area)","usd_low": 100,"usd_high": 400,"cad_low": 150,"cad_high": 500,"trade": "Drywall Contractor / Handyman","note": "Hole or damage repair up to 1 sq ft"},
    "INT_DRYWALL_LARGE": {"display": "Drywall repair (large area)","usd_low": 400,"usd_high": 2000,"cad_low": 500,"cad_high": 2500,"trade": "Drywall Contractor","note": "Panel replacement and finishing"},
    "INT_CLOSET_LIGHT": {"display": "Closet light / unprotected bulb correction","usd_low": 75,"usd_high": 200,"cad_low": 100,"cad_high": 250,"trade": "Electrician","note": "Globe or enclosed fixture installation"},

    # BATHROOM
    "BATH_SHOWER_CAULK": {"display": "Shower / tub sealant and caulking","usd_low": 100,"usd_high": 400,"cad_low": 150,"cad_high": 500,"trade": "Handyman / Tile Specialist","note": "Full recaulk of shower or tub surround"},
    "BATH_SHOWER_CAULK_MOLD": {"display": "Shower caulk replacement with mold remediation","usd_low": 200,"usd_high": 700,"cad_low": 250,"cad_high": 900,"trade": "Handyman / Mold Remediation","note": "Remove, treat and reseal; extent of mold may increase cost"},
    "BATH_TOILET_RESET": {"display": "Toilet reset / resecuring","usd_low": 150,"usd_high": 350,"cad_low": 200,"cad_high": 450,"trade": "Plumber","note": "Includes new wax ring and re-bolt to floor"},
    "BATH_TOILET_WAX_RING": {"display": "Toilet wax ring replacement","usd_low": 150,"usd_high": 300,"cad_low": 200,"cad_high": 400,"trade": "Plumber","note": "Remove toilet, replace ring, reset and reseal"},
    "BATH_SINK_STOPPER": {"display": "Sink stopper repair or replacement","usd_low": 75,"usd_high": 200,"cad_low": 100,"cad_high": 250,"trade": "Plumber / Handyman","note": "Drain assembly adjustment or part replacement"},
    "BATH_FAUCET_LOOSE": {"display": "Loose faucet resecuring","usd_low": 75,"usd_high": 200,"cad_low": 100,"cad_high": 250,"trade": "Plumber / Handyman","note": "Tighten mounting nut or replace faucet hardware"},
    "BATH_SHOWER_LEAK": {"display": "Active shower / tub leak repair","usd_low": 400,"usd_high": 1500,"cad_low": 500,"cad_high": 2000,"trade": "Plumber / Tile Specialist","note": "Diagnosis and repair; tile removal may be required"},
    "BATH_SHOWER_HEAD_LEAK": {"display": "Shower head leak repair","usd_low": 75,"usd_high": 250,"cad_low": 100,"cad_high": 300,"trade": "Plumber / Handyman","note": "Washer, cartridge or head replacement"},
    "BATH_BASEBOARD": {"display": "Bathroom baseboard reattachment / repair","usd_low": 75,"usd_high": 300,"cad_low": 100,"cad_high": 400,"trade": "Carpenter / Handyman","note": "Reattach, caulk and paint; moisture source should be addressed"},
    "BATH_WINDOW_TRIM": {"display": "Bathroom window trim repair","usd_low": 100,"usd_high": 400,"cad_low": 150,"cad_high": 500,"trade": "Carpenter / Handyman","note": "Crack repair or trim replacement"},
    "BATH_WALL_HEATER": {"display": "Bathroom wall heater repair or replacement","usd_low": 150,"usd_high": 600,"cad_low": 200,"cad_high": 750,"trade": "Electrician / HVAC Technician","note": "Electric unit replacement; gas units higher"},
    "BATH_MOISTURE_DAMAGE": {"display": "Bathroom moisture damage repair","usd_low": 300,"usd_high": 2500,"cad_low": 400,"cad_high": 3000,"trade": "General Contractor / Water Damage Restoration","note": "Scope varies; includes drywall, subfloor, or tile repair"},

    # LAUNDRY
    "LAUNDRY_MOLD": {"display": "Laundry / washer mold cleaning","usd_low": 100,"usd_high": 400,"cad_low": 150,"cad_high": 500,"trade": "Handyman / Mold Remediation","note": "Machine cleaning; persistent mold may require remediation"},

    # ASBESTOS
    "ASBESTOS_TEST": {"display": "Asbestos testing","usd_low": 300,"usd_high": 900,"cad_low": 400,"cad_high": 1100,"trade": "Asbestos Testing Specialist","note": "Bulk sample collection and lab analysis"},
    "ASBESTOS_INTERIOR": {"display": "Asbestos abatement (interior material)","usd_low": 1500,"usd_high": 10000,"cad_low": 2000,"cad_high": 12000,"trade": "Asbestos Abatement Contractor","note": "Costs vary greatly by material type, quantity and containment needs"},
    "ASBESTOS_POPCORN": {"display": "Popcorn ceiling asbestos removal","usd_low": 1000,"usd_high": 6000,"cad_low": 1200,"cad_high": 7500,"trade": "Asbestos Abatement Contractor","note": "Per room or whole home; testing required before work"},
}

# Merge extended entries into main COST_TABLE
COST_TABLE.update(_EXTENDED)