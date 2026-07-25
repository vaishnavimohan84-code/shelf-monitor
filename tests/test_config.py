import importlib
import os
import sys
import unittest


class ConfigDatabaseUriTests(unittest.TestCase):
    def test_password_with_special_characters_is_url_encoded(self):
        os.environ["DB_HOST"] = "127.0.0.1"
        os.environ["DB_PORT"] = "3306"
        os.environ["DB_NAME"] = "shelf_monitor"
        os.environ["DB_USER"] = "root"
        os.environ["DB_PASSWORD"] = "Vaishu@2003"
        os.environ["DB_USE_SQLITE"] = "false"
        os.environ["DB_SKIP_CONNECTION_CHECK"] = "true"

        sys.modules.pop("config", None)
        config = importlib.import_module("config")

        uri = config.build_database_uri()

        self.assertIn("root:Vaishu%402003", uri)
        self.assertNotIn("root:Vaishu@2003@127.0.0.1", uri)

    def test_sqlite_is_used_when_requested(self):
        os.environ["DB_USE_SQLITE"] = "true"
        os.environ["DB_HOST"] = "127.0.0.1"
        os.environ["DB_PORT"] = "3306"
        os.environ["DB_NAME"] = "shelf_monitor"
        os.environ["DB_USER"] = "root"
        os.environ["DB_PASSWORD"] = "Vaishu@2003"
        os.environ["DB_SKIP_CONNECTION_CHECK"] = "true"

        sys.modules.pop("config", None)
        config = importlib.import_module("config")

        uri = config.Config.SQLALCHEMY_DATABASE_URI

        self.assertTrue(uri.startswith("sqlite:///"))


if __name__ == "__main__":
    unittest.main()
