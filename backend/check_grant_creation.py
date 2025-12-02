
import requests
import json

# 1. Login as PI
session = requests.Session()
login_payload = {'email': 'pi@mubas.ac.mw', 'password': 'mubas123'}
login_res = session.post('http://localhost:5000/api/login', json=login_payload)
print(f"Login Status: {login_res.status_code}")
if login_res.status_code != 200:
    print(login_res.text)
    exit(1)

# 2. Create Dummy Files
files = {
    'agreement': ('agreement.pdf', b'%PDF-1.4 dummy content', 'application/pdf'),
    'budget_breakdown': ('budget.xlsx', b'dummy excel content', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
    'award_letter': ('award.pdf', b'%PDF-1.4 dummy award', 'application/pdf'),
    'ethical_approval': ('ethics.pdf', b'%PDF-1.4 dummy ethics', 'application/pdf'),
    'milestone_evidence_0': ('evidence.jpg', b'dummy_image', 'image/jpeg')
}

# 3. Create Payload
payload = {
    'title': 'Test Grant 2024',
    'funder': 'World Bank',
    'grant_code': 'WB-TEST-001',
    'funder_reference_number': 'REF-12345',
    'start_date': '2024-01-01',
    'end_date': '2024-12-31',
    'total_budget': '100000',
    'currency': 'USD',
    'exchange_rate': '1700',
    'financial_reporting_frequency': 'quarterly',
    'progress_reporting_frequency': 'biannual',
    'special_requirements': 'None',
    'budget_categories': json.dumps([
        {'name': 'Salaries', 'allocated': '50000'},
        {'name': 'Equipment', 'allocated': '50000'}
    ]),
    'milestones': json.dumps([
        {
            'title': 'Milestone 1',
            'due_date': '2024-06-30',
            'reporting_period': 'interim',
            'status': 'not_started'
        }
    ]),
    'team_members': json.dumps([])
}

# 4. Submit
print("Submitting Grant...")
res = session.post('http://localhost:5000/api/grants', data=payload, files=files)
print(f"Grant Creation Status: {res.status_code}")
print(res.text)
