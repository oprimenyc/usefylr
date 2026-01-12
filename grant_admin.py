"""
Grant admin access to a user
Usage: python grant_admin.py <email>
"""

import sys
from app import create_app, db
from app.models import User

def grant_admin(email):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"User with email {email} not found")
            return False

        user.is_admin = True
        db.session.commit()
        print(f"Admin access granted to {user.email} (username: {user.username})")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python grant_admin.py <email>")
        print("Example: python grant_admin.py tester@usefylr.app")
        sys.exit(1)

    email = sys.argv[1]
    success = grant_admin(email)
    sys.exit(0 if success else 1)
