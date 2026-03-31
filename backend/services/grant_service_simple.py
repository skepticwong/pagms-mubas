import os
import json
from datetime import datetime, date
from werkzeug.utils import secure_filename
from models import db, Grant, BudgetCategory, User, AuditLog, Milestone

class GrantServiceSimple:
    @staticmethod
    def get_grants_for_user(user_id):
        """
        Simplified version of get_grants_for_user that avoids complex relationships
        """
        print(f"DEBUG: Simple get_grants_for_user called with user_id: {user_id}")
        
        try:
            # Get user
            user = User.query.get(user_id)
            if not user:
                print(f"DEBUG: No user found for user_id {user_id}")
                return []
                
            print(f"DEBUG: User role for user_id {user_id}: {user.role}")
            
            # Simple grant query based on role
            # Query grants based on role or team membership
            if user.role == 'RSU':
                grants = Grant.query.order_by(Grant.created_at.desc()).all()
            elif user.role == 'PI':
                # Primary PI sees their own grants
                grants = Grant.query.filter_by(pi_id=user_id).order_by(Grant.created_at.desc()).all()
            else:
                # For Team members, Co-PIs, etc., get grants through team membership
                from models import GrantTeam
                team_memberships = GrantTeam.query.filter_by(user_id=user_id).all()
                grant_ids = [tm.grant_id for tm in team_memberships]
                # Also include if they are the primary PI (backup check)
                grants = Grant.query.filter((Grant.pi_id == user_id) | (Grant.id.in_(grant_ids)))\
                    .order_by(Grant.created_at.desc()).all()

            results = []
            
            for grant in grants:
                try:
                    # Simple data extraction - avoid complex relationships
                    user_role = "PI" if grant.pi_id == user_id else "Co-PI"
                    
                    # Basic financials - direct query to avoid relationship issues
                    categories = BudgetCategory.query.filter_by(grant_id=grant.id).all()
                    total_budget = float(grant.total_budget or 0.0)
                    total_spent = sum((cat.spent or 0.0) for cat in categories)
                    spent_percent = (total_spent / total_budget * 100) if total_budget > 0 else 0
                    
                    # Simple milestone count
                    milestones = Milestone.query.filter_by(grant_id=grant.id).all()
                    completed_milestones = [m for m in milestones if m.status == 'completed']
                    milestone_completion_rate = (len(completed_milestones) / len(milestones) * 100) if milestones else 0
                    
                    # Calculate Burn Rate (time vs spend)
                    today = date.today()
                    grant_start_date = grant.start_date or today
                    grant_end_date = grant.end_date or today
                    
                    total_days = (grant_end_date - grant_start_date).days
                    days_elapsed = (today - grant_start_date).days
                    time_elapsed_pct = max(0.0, min(100.0, (float(days_elapsed) / float(total_days) * 100.0)) if total_days > 0 else 0.0)
                    
                    burn_rate_status = "normal"
                    burn_rate_diff = spent_percent - time_elapsed_pct
                    if burn_rate_diff > 15:
                        burn_rate_status = "high"
                    elif burn_rate_diff < -15:
                        burn_rate_status = "low"
                    
                    # Create burn rate object
                    burn_rate = {
                        'time_elapsed_pct': round(time_elapsed_pct, 1),
                        'spend_pct': spent_percent,
                        'status': burn_rate_status,
                        'difference': round(burn_rate_diff, 1)
                    }
                    
                    # Basic data dict
                    data = {
                        'id': grant.id,
                        'title': grant.title,
                        'funder': grant.funder,
                        'grant_code': grant.grant_code,
                        'total_budget': total_budget,
                        'status': grant.status,
                        'disbursement_type': grant.disbursement_type,
                        'start_date': grant.start_date.isoformat() if grant.start_date else None,
                        'end_date': grant.end_date.isoformat() if grant.end_date else None,
                        'pi_id': grant.pi_id,
                        'pi': {
                            'name': grant.pi.name if grant.pi else 'N/A',
                            'email': grant.pi.email if grant.pi else 'N/A'
                        },
                        'user_role': user_role,
                        'spent_percent': round(spent_percent, 1),
                        'milestone_completion_rate': round(milestone_completion_rate, 1),
                        'categories_count': len(categories),
                        'milestones_count': len(milestones),
                        'burn_rate': burn_rate,
                        'categories': [c.to_dict() for c in categories],
                        'created_at': grant.created_at.isoformat() if grant.created_at else None,
                        
                        # Ethics Compliance Fields
                        'ethics_required': grant.ethics_required,
                        'ethics_status': grant.ethics_status or 'NOT_SUBMITTED',
                        'ethics_expiry_date': grant.ethics_expiry_date.isoformat() if grant.ethics_expiry_date else None,
                        'ethics_approval_number': grant.ethics_approval_number,
                        'ethics_certificate_filename': grant.ethics_certificate_filename
                    }
                    
                    results.append(data)
                    
                except Exception as e:
                    print(f"Error processing grant {grant.id}: {e}")
                    # Skip this grant but continue with others
                    continue
            
            print(f"DEBUG: Simple get_grants_for_user returning {len(results)} grants")
            return results
            
        except Exception as e:
            print(f"ERROR in get_grants_for_user: {e}")
            import traceback
            traceback.print_exc()
            return []
