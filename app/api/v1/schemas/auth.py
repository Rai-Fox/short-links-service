from pydantic import BaseModel

from core.security import verify_password, get_password_hash


class UserBase(BaseModel):
    username: str


class UserRegister(UserBase):
    password: str

    @property
    def hashed_password(self) -> str:
        return get_password_hash(self.password)


class UserLogin(UserBase):
    password: str


class UserInDB(UserBase):
    hashed_password: str

    def verify_password(self, password: str) -> bool:
        return verify_password(password, self.hashed_password)
