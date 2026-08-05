from unittest.mock import AsyncMock, patch

from sqlalchemy.exc import SQLAlchemyError

from backend.src import main

from support import AppTestCase


class RegistrationTests(AppTestCase):
    def test_registration_hashes_password_and_logs_user_in(self) -> None:
        response = self.register(email="MixedCase@Example.com")

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["email"], "mixedcase@example.com")
        self.assertNotIn("password", response.json())
        self.assertNotIn("password_hash", response.json())
        self.assertNotIn("is_admin", response.json())
        self.assertEqual(self.client.get("/users/me").status_code, 200)

        rows = self.database_rows(
            "SELECT email, password_hash, is_admin FROM users"
        )
        self.assertEqual(rows[0][0], "mixedcase@example.com")
        self.assertNotEqual(rows[0][1], "password123")
        self.assertEqual(rows[0][2], 0)

    def test_guest_entries_are_saved_during_registration(self) -> None:
        self.assertEqual(
            self.client.post("/insert", params={"word": "Guest Apple"}).status_code,
            200,
        )
        self.assertEqual(
            self.client.post("/insert", params={"word": "Guest Banana"}).status_code,
            200,
        )
        guest_identity = self.identity_with_prefix("guest:")

        response = self.register()

        self.assertEqual(response.status_code, 201, response.text)
        self.assertNotIn(guest_identity, main.app.state.roots)
        self.assertEqual(
            self.database_rows(
                """
                SELECT users.email, dict_entries.entry
                FROM users
                JOIN dict_entries ON dict_entries.user_id = users.id
                ORDER BY dict_entries.entry
                """
            ),
            [
                ("user@example.com", "Guest Apple"),
                ("user@example.com", "Guest Banana"),
            ],
        )
        self.assertEqual(
            self.client.get("/search", params={"prefix": "Guest"}).json(),
            {"words": ["Guest Apple", "Guest Banana"]},
        )

    def test_duplicate_email_keeps_guest_session_and_entries(self) -> None:
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.client.post("/users/logout").status_code, 204)
        self.assertEqual(
            self.client.post("/insert", params={"word": "Keep Me"}).status_code,
            200,
        )
        guest_identity = self.identity_with_prefix("guest:")

        response = self.register(email="USER@example.com")

        self.assertEqual(response.status_code, 409)
        self.assertIn(guest_identity, main.app.state.roots)
        self.assertEqual(
            self.client.get("/search", params={"prefix": "Keep"}).json(),
            {"words": ["Keep Me"]},
        )

    def test_database_failure_keeps_guest_trie(self) -> None:
        self.assertEqual(
            self.client.post("/insert", params={"word": "Still Here"}).status_code,
            200,
        )
        guest_identity = self.identity_with_prefix("guest:")

        with patch(
            "backend.src.routers.users.create_user_with_entries",
            new=AsyncMock(side_effect=SQLAlchemyError("database unavailable")),
        ):
            response = self.register()

        self.assertEqual(response.status_code, 500)
        self.assertIn(guest_identity, main.app.state.roots)
        self.assertEqual(
            self.client.get("/search", params={"prefix": "Still"}).json(),
            {"words": ["Still Here"]},
        )
        self.assertEqual(self.database_rows("SELECT id FROM users"), [])


class LoginAndSessionTests(AppTestCase):
    def test_login_rejects_bad_credentials_and_accepts_correct_password(self) -> None:
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.client.post("/users/logout").status_code, 204)

        wrong = self.login(password="wrong-password")
        self.assertEqual(wrong.status_code, 401)

        correct = self.login()
        self.assertEqual(correct.status_code, 200, correct.text)
        self.assertEqual(self.client.get("/users/me").status_code, 200)

    def test_logout_removes_authenticated_access(self) -> None:
        self.assertEqual(self.register().status_code, 201)

        self.assertEqual(self.client.post("/users/logout").status_code, 204)
        self.assertEqual(self.client.get("/users/me").status_code, 401)

    def test_cookie_for_deleted_user_becomes_a_guest_identity(self) -> None:
        registered = self.register()
        self.assertEqual(registered.status_code, 201)
        user_id = registered.json()["id"]
        self.execute_sql("DELETE FROM users WHERE id = ?", (user_id,))

        self.assertEqual(self.client.get("/users/me").status_code, 401)
        inserted = self.client.post("/insert", params={"word": "Guest Again"})
        self.assertEqual(inserted.status_code, 200, inserted.text)
        self.assertTrue(self.identity_with_prefix("guest:").startswith("guest:"))


if __name__ == "__main__":
    import unittest

    unittest.main()
