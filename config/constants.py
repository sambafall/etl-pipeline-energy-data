"""
Configuration constants for the ETL pipeline.
"""

# Energy sources to extract and analyze
ENERGY_SOURCES = [
    'thermique_mw',
    'nucléaire_mw',
    'eolien_mw',
    'solaire_mw',
    'hydraulique_mw',
    'pompage_mw',
    'bioénergies_mw'
]

# Renewable energy sources to include in analysis
RENEWABLE_SOURCES = [
    'eolien_mw',
    'solaire_mw',
    'hydraulique_mw'
]

# Columns to extract from raw data
RAW_COLUMNS = [
    'région',
    'date_heure',
    'thermique_mw',
    'nucléaire_mw',
    'eolien_mw',
    'solaire_mw',
    'hydraulique_mw',
    'pompage_mw',
    'bioénergies_mw'
]

# Database configuration
DB_SCHEMA = 'energy'
DB_TABLE = 'eco_to_mix'

# API configuration
ECO2MIX_API_BASE_URL = 'https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-regional-tr/exports/csv'
ECO2MIX_API_PARAMS = {
    'lang': 'fr',
    'refine': 'date_heure:"2024"',
    'facet': 'facet(name="libelle_region")'
}

# Data validation
MIN_ROWS_THRESHOLD = 100
REQUIRED_COLUMNS = RAW_COLUMNS
