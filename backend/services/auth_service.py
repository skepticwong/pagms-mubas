# backend/services/auth_service.py
from models import db, User

class AuthService:
    @staticmethod
    def login(email, password):
        """
        Authenticate user by email + password
        Returns User object or None
        """
        if not email or not password:
            raise ValueError("Email and password are required")
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def register(name, email, password, role='Team', pay_rate=None):
        """
        Register a new user with validation
        Returns User object
        Raises ValueError on validation errors
        """
        # Validation
        if not name or not email or not password:
            raise ValueError("Name, email, and password are required")
        
        # Validate email format (basic check)
        if '@' not in email:
            raise ValueError("Invalid email format")
        
        # Validate password length
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        
        # Validate role
        valid_roles = ['PI', 'Team', 'Finance', 'RSU']
        if role not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            raise ValueError("User with this email already exists")
        
        # Create user
        user = User(
            name=name,
            email=email,
            role=role,
            pay_rate=pay_rate
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def create_user(name, email, role, password, pay_rate=None):
        """
        Create a new user (for seeding, bypasses some validations)
        Returns User object
        """
        if User.query.filter_by(email=email).first():
            raise ValueError("User with this email already exists")
        
        user = User(
            name=name,
            email=email,
            role=role,
            pay_rate=pay_rate
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def get_user_by_id(user_id):
        """
        Get user by ID
        Returns User object or None
        """
        if not user_id:
            return None
        return User.query.get(user_id)