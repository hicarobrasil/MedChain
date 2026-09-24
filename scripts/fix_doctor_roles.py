"""
Script para corrigir role em auth_users: define role='doctor' para emails que têm DoctorModel.
Execute: python -m scripts.fix_doctor_roles
"""
import sys
from pathlib import Path

# adiciona raiz do projeto ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_db
from app.models.login_record import User
from app.models.user import UserModel
from app.models.doctor import DoctorModel
from app.auth.service import UserService

def main():
    db = next(get_db())
    user_service = UserService()
    updated = 0
    for doctor in db.query(DoctorModel).join(UserModel).all():
        email = doctor.user.email
        auth_user = user_service.get_user_by_email(email, db)
        if auth_user and (auth_user.role or "").lower() != "doctor":
            user_service.update_user(auth_user, {"role": "doctor"}, db)
            print(f"  Atualizado: {email} -> role=doctor")
            updated += 1
    print(f"\nConcluído. {updated} médico(s) atualizado(s).")

if __name__ == "__main__":
    main()
