import bcrypt


def hash_password(plainPassword: str) -> str:
    return bcrypt.hashpw(plainPassword.encode(), bcrypt.gensalt()).decode()


def verify_password(plainPassword: str, hashedPassword: str) -> bool:
    return bcrypt.checkpw(plainPassword.encode(), hashedPassword.encode())
