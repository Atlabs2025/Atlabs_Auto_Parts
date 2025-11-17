{
    "name": "Google Sheet Vehicle Sync (CSV Import)",
    "version": "1.0.0",
    "summary": "Import vehicles from a Google Sheet CSV link",
    "description": "Import Vehicles from a Google Sheet using CSV export.",
    "author": "ChatGPT",
    "category": "Tools",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/vehicle_details_views.xml",
        "views/vehicle_google_import_view.xml",
        "views/vehicle_menu.xml",
        "data/vehicle_import_cron.xml",

    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3"
}
