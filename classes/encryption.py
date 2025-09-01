import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv('.env')
EncryptionKey = os.getenv("KEY")

class Encryption :
    def __init__(self) :
        self.fernet = Fernet(EncryptionKey)

    def encrypt(self, text: str) -> str :
        """Encrypts the text"""
        return str(self.fernet.encrypt(text.encode()))

    def decrypt(self, text: bytes | str) -> str :
        """Decrypts the text"""
        if text is None :
            return "No Dob Stored"
        if text.startswith("b'") and text.endswith("'") :
            text = text[2 :-1]
        if text.startswith('b"') and text.endswith('"') :
            text = text[2 :-1]
        return self.fernet.decrypt(text).decode()

