from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash


app = create_app()

with app.app_context():

    name = input("Enter admin name: ").strip()
    email = input("Enter admin email: ").strip()
    password = input("Enter admin password: ").strip()

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:

        if existing_user.role.lower() == "admin":
            existing_user.role = "ADMIN"
            db.session.commit()

            print("Existing admin account updated successfully.")

        else:
            print("A user with this email already exists.")
            print("No changes were made.")

    else:

        admin = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="ADMIN"
        )

        db.session.add(admin)
        db.session.commit()

        print("Admin account created successfully.")