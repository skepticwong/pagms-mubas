
import os
import sys
from flask import Flask

# Add backend to path
sys.path.append(os.getcwd())

from backend.app import create_app
from backend.models import db, RuleProfile

app = create_app()

TEMPLATES = {
    'wb': 'World_Bank_Reporting_Template_v2.docx',
    'usaid': 'USAID_Standard_Funder_Report.pdf',
    'nrf': 'NRF_Malawi_Grant_Progress_Form.docx',
    'dfid': 'DFID_Annual_Review_Template.pdf',
    'gates': 'Gates_Foundation_Outcome_Tracker.xlsx'
}

with app.app_context():
    print("Seeding common templates...")
    for funder_id, template in TEMPLATES.items():
        # Find the active profile for this funder
        profile = RuleProfile.query.filter_by(funder_id=funder_id, is_active=True).first()
        if profile:
            if not profile.reporting_template_filename:
                profile.reporting_template_filename = template
                print(f"Updated {funder_id} with template: {template}")
            else:
                print(f"Skipping {funder_id}, already has: {profile.reporting_template_filename}")
        else:
            print(f"No active profile found for {funder_id}. Creating a placeholder profile...")
            # If no profile exists, we create a basic one so the template can be stored
            new_profile = RuleProfile(
                name=f"Standard {funder_id.upper()} Compliance Profile",
                funder_id=funder_id,
                is_active=True,
                created_by_id=4, # RSU Admin
                reporting_template_filename=template
            )
            db.session.add(new_profile)
            print(f"Created new profile for {funder_id} with template: {template}")
    
    db.session.commit()
    print("Seeding complete.")
