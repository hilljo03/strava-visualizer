import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

_fernet = Fernet(os.environ["TOKEN_ENCRYPTION_KEY"].encode())


def encrypt_token(token: str) -> str:
    return _fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    return _fernet.decrypt(encrypted.encode()).decode()
