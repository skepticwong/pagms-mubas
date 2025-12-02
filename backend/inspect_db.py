
from app import create_app
from models import db, Grant, User, BudgetCategory, Milestone, GrantTeam # Import GrantTeam

app = create_app()

def inspect_database():
    separator = "-" * 80
    with app.app_context():
        print("\n🔍 INSPECTING DATABASE CONTENTS")
        
        # 1. Check Users
        print(f"\n{separator}")
        print("👥 USERS")
        users = User.query.all()
        print(f"Total: {len(users)}")
        for u in users:
            print(f" - ID: {u.id} | {u.name} ({u.role}) - {u.email}")

        # 2. Check Grants
        print(f"\n{separator}")
        print("📜 GRANTS")
        grants = Grant.query.all()
        print(f"Total: {len(grants)}")
        for g in grants:
            pi_name = g.pi.name if g.pi else "Unknown PI"
            print(f" - ID: {g.id} | [{g.status.upper()}] {g.title}")
            print(f"   Code: {g.grant_code} | Funder: {g.funder}")
            print(f"   Budget: ${g.total_budget:,.2f} | Spent: {calc_spent_percent(g)}%")
            print(f"   PI: {pi_name}")
            
            # Display Budget Categories
            if g.categories:
                print("   Budget Categories:")
                for category in g.categories:
                    print(f"     - {category.name}: Allocated ${category.allocated:,.2f}, Spent ${category.spent:,.2f}")
            
            # Display Milestones
            if g.milestones:
                print("   Milestones:")
                for milestone in g.milestones:
                    print(f"     - {milestone.title} (Due: {milestone.due_date}, Status: {milestone.status}, Period: {milestone.reporting_period})")
            
            print("")

        # 3. Check Grant Team
        print(f"\n{separator}")
        print("🤝 GRANT TEAM")
        grant_teams = GrantTeam.query.all()
        print(f"Total: {len(grant_teams)}")
        for gt in grant_teams:
            print(f" - ID: {gt.id} | Grant ID: {gt.grant_id} | User ID: {gt.user_id} ({gt.user.name}) | Role: {gt.role} | Added: {gt.date_added.strftime('%Y-%m-%d')}")

def calc_spent_percent(grant):
    if not grant.categories or grant.total_budget == 0:
        return 0
    total_spent = sum(c.spent for c in grant.categories)
    return round((total_spent / grant.total_budget) * 100, 1)

if __name__ == "__main__":
    inspect_database()
