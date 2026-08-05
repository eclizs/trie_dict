import unittest
from uuid import uuid4

from pydantic import ValidationError

from backend.src.auth import hash_password, verify_password
from backend.src.dependencies import get_user_id, identity_is_valid
from backend.src.schema import UserCreate, UserLogin


class PasswordTests(unittest.TestCase):
    def test_passwords_are_hashed_and_verified(self) -> None:
        password = "correct horse battery staple"
        password_hash = hash_password(password)

        self.assertNotEqual(password_hash, password)
        self.assertTrue(verify_password(password, password_hash))
        self.assertFalse(verify_password("wrong password", password_hash))


class IdentityTests(unittest.TestCase):
    def test_valid_user_and_guest_identities(self) -> None:
        guest_identity = f"guest:{uuid4()}"

        self.assertTrue(identity_is_valid("user:1"))
        self.assertTrue(identity_is_valid(guest_identity))
        self.assertEqual(get_user_id("user:42"), 42)
        self.assertEqual(get_user_id(guest_identity), -1)

    def test_invalid_identities_are_rejected(self) -> None:
        invalid_identities = (
            None,
            123,
            "",
            "user:0",
            "user:-1",
            "user:not-a-number",
            "guest:not-a-uuid",
            "unknown:1",
        )

        for identity in invalid_identities:
            with self.subTest(identity=identity):
                self.assertFalse(identity_is_valid(identity))

        with self.assertRaises(ValueError):
            get_user_id("unknown:1")


class SchemaTests(unittest.TestCase):
    def test_registration_requires_a_valid_email_and_password_length(self) -> None:
        with self.assertRaises(ValidationError):
            UserCreate(email="not-an-email", password="password123")

        with self.assertRaises(ValidationError):
            UserCreate(email="user@example.com", password="short")

    def test_login_accepts_a_nonempty_password(self) -> None:
        login = UserLogin(email="user@example.com", password="x")
        self.assertEqual(login.password, "x")

        with self.assertRaises(ValidationError):
            UserLogin(email="user@example.com", password="")


if __name__ == "__main__":
    unittest.main()
