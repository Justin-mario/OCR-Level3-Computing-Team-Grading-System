from app import create_app, db
from app.models.entities import Admin

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()

    # Create default admin if doesn't exist
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(
            username='admin',
            email='admin@example.com'
        )
        admin.set_password('password')  # Change this!
        db.session.add(admin)
        db.session.commit()