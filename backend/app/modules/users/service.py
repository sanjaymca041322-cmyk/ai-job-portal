import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate
from app.modules.users.security import hash_password


class DuplicateEmailError(Exception):
    pass


class UserService:
    def __init__(self, session: Session) -> None:
        self.repository = UserRepository(session)
        self.session = session

    def create_user(self, user_data: UserCreate) -> User:
        if self.repository.get_by_email(str(user_data.email)) is not None:
            raise DuplicateEmailError

        user = User(
            email=str(user_data.email),
            password_hash=hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
        )

        try:
            created_user = self.repository.create(user)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateEmailError from exc

        self.session.refresh(created_user)
        return created_user

    def get_user(self, user_id: uuid.UUID) -> User | None:
        return self.repository.get_by_id(user_id)