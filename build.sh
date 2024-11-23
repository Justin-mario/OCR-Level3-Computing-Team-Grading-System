#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Initialize the database
python init_db.py


#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Create init_db.py if it doesn't exist
if [ ! -f "init_db.py" ]; then
    echo "from app import create_app, db
from app.models.entities import Admin

app = create_app()

with app.app_context():
    db.create_all()

    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(
            username='admin',
            email='admin@example.com'
        )
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()" > init_db.py
fi

python init_db.py