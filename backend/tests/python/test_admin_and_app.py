from backend.src import main

from support import AppTestCase


class AdminImportTests(AppTestCase):
    def upload_csv(self, contents: str):
        return self.client.post(
            "/insert_excel",
            files={"file": ("entries.csv", contents, "text/csv")},
        )

    def test_guest_and_regular_user_cannot_import_csv(self) -> None:
        self.assertEqual(
            self.upload_csv("A,C,Guest Item,1,item,1\n").status_code,
            403,
        )

        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(
            self.upload_csv("A,C,User Item,1,item,1\n").status_code,
            403,
        )

    def test_admin_can_import_entries_and_duplicates_are_reported(self) -> None:
        registered = self.register(email="admin@example.com")
        self.assertEqual(registered.status_code, 201, registered.text)
        self.execute_sql(
            "UPDATE users SET is_admin = 1 WHERE email = ?",
            ("admin@example.com",),
        )

        response = self.upload_csv(
            "A,C,Imported Apple,1,item,1\n"
            "B,D,Imported Banana,2,item,2\n"
            "C,E,Imported Apple,3,item,3\n"
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            response.json(),
            {
                "inserted": ["Imported Apple", "Imported Banana"],
                "failed": [
                    {
                        "word": "Imported Apple",
                        "reason": "'Imported Apple' already exists",
                    }
                ],
            },
        )
        self.assertEqual(
            self.database_rows(
                "SELECT entry FROM dict_entries ORDER BY entry"
            ),
            [("Imported Apple",), ("Imported Banana",)],
        )


class ApplicationTests(AppTestCase):
    def test_frontend_and_static_files_are_served(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<title>orderan</title>", response.text)

        stylesheet = self.client.get("/static/style.css")
        self.assertEqual(stylesheet.status_code, 200)
        self.assertIn("text/css", stylesheet.headers["content-type"])

    def test_hidden_admin_route_is_not_in_openapi(self) -> None:
        paths = main.app.openapi()["paths"]
        self.assertNotIn("/insert_excel", paths)


if __name__ == "__main__":
    import unittest

    unittest.main()
