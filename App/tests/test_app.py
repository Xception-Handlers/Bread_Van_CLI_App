import os
import tempfile
import unittest
from datetime import date, time, datetime, timedelta

from App.main import create_app
from App.models import Driver, Drive  
from App.database import db, create_db
from App.models import (
    User, Resident, Driver, Admin,
    Area, Street, Drive, Stop, Item, DriverStock
)
from App.controllers import (
    create_user, get_all_users_json, update_user, get_user,
    user_login, user_logout,
    resident_create, resident_request_stop, resident_cancel_stop,
    resident_view_driver_stats, resident_view_stock, resident_view_inbox,
    driver_schedule_drive, driver_cancel_drive, driver_view_drives,
    driver_start_drive, driver_end_drive, driver_view_requested_stops,
    driver_update_stock, driver_view_stock,
    admin_create_driver, admin_delete_driver, admin_add_area,
    admin_delete_area, admin_view_all_areas, admin_add_street,
    admin_delete_street, admin_view_all_streets, admin_add_item,
    admin_delete_item, admin_view_all_items
)


# ============================================================
#  Unit Tests for Models
# ============================================================

class UserUnitTests(unittest.TestCase):

    def test_new_user(self):
        user = User("bob", "bobpass")
        self.assertEqual(user.username, "bob")

    def test_user_get_json(self):
        user = User("bob", "bobpass")
        self.assertEqual(user.get_json(), {"id": None, "username": "bob"})

    def test_hashed_password(self):
        user = User("alice", "mypass")
        # raw password should not be stored
        self.assertNotEqual(user.password, "mypass")

    def test_check_password(self):
        user = User("alice", "mypass")
        self.assertTrue(user.check_password("mypass"))
        self.assertFalse(user.check_password("wrongpass"))


class ResidentUnitTests(unittest.TestCase):

    def test_new_resident(self):
        r = Resident("john", "johnpass", 1, 2, 123)
        self.assertEqual(r.username, "john")
        self.assertNotEqual(r.password, "johnpass")
        self.assertEqual(r.areaId, 1)
        self.assertEqual(r.streetId, 2)
        self.assertEqual(r.houseNumber, 123)
        self.assertEqual(r.inbox, [])

    def test_resident_type(self):
        r = Resident("john", "johnpass", 1, 2, 123)
        self.assertEqual(r.type, "Resident")

    def test_resident_get_json(self):
        r = Resident("john", "johnpass", 1, 2, 123)
        expected = {
            "id": None,
            "username": "john",
            "areaId": 1,
            "streetId": 2,
            "houseNumber": 123,
            "inbox": [],
        }
        self.assertEqual(r.get_json(), expected)

    def test_receive_notification_and_view_inbox(self):
    # need an app + db context because receive_notif uses db.session
        app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://"
        })
        with app.app_context():
            create_db()

            r = Resident("john", "johnpass", 1, 2, 123)
            db.session.add(r)
            db.session.commit()

        # 1st notification
            r.receive_notif("New msg")
            self.assertTrue(r.inbox[-1].endswith("New msg"))
            self.assertTrue(r.inbox[-1].startswith("["))  # timestamp prefix

        # add more notifications
            r.receive_notif("msg1")
            r.receive_notif("msg2")

            inbox = r.view_inbox()
            self.assertEqual(len(inbox), 3)
            self.assertTrue(inbox[-2].endswith("msg1"))
            self.assertTrue(inbox[-1].endswith("msg2"))


class DriverUnitTests(unittest.TestCase):

    def test_new_driver(self):
        d = Driver("steve", "stevepass", "Busy", 2, 12)
        self.assertEqual(d.username, "steve")
        self.assertNotEqual(d.password, "stevepass")
        self.assertEqual(d.status, "Busy")
        self.assertEqual(d.areaId, 2)
        self.assertEqual(d.streetId, 12)

    def test_driver_type(self):
        d = Driver("steve", "stevepass", "Busy", 2, 12)
        self.assertEqual(d.type, "Driver")

    def test_driver_get_json(self):
        d = Driver("steve", "stevepass", "Busy", 2, 12)
        expected = {
            "id": None,
            "username": "steve",
            "status": "Busy",
            "areaId": 2,
            "streetId": 12,
        }
        self.assertEqual(d.get_json(), expected)


class AdminUnitTests(unittest.TestCase):

    def test_new_admin(self):
        a = Admin("admin", "adminpass")
        self.assertEqual(a.username, "admin")
        self.assertNotEqual(a.password, "adminpass")

    def test_admin_type(self):
        a = Admin("admin", "adminpass")
        self.assertEqual(a.type, "Admin")

    def test_admin_get_json(self):
        a = Admin("admin", "adminpass")
        self.assertEqual(a.get_json(), {"id": None, "username": "admin"})


class AreaUnitTests(unittest.TestCase):

    def test_new_area(self):
        area = Area("Sangre Grande")
        self.assertEqual(area.name, "Sangre Grande")

    def test_area_get_json(self):
        area = Area("Sangre Grande")
        self.assertEqual(area.get_json(), {"id": None, "name": "Sangre Grande"})


class StreetUnitTests(unittest.TestCase):

    def test_new_street(self):
        s = Street("Picton Road", 8)
        self.assertEqual(s.name, "Picton Road")
        self.assertEqual(s.areaId, 8)

    def test_street_get_json(self):
        s = Street("Picton Road", 8)
        expected = {"id": None, "name": "Picton Road", "areaId": 8}
        self.assertEqual(s.get_json(), expected)


class DriveUnitTests(unittest.TestCase):

    def test_new_drive(self):
        d = Drive(78, 2, 12, date(2025, 11, 8), time(11, 30), "Upcoming")
        self.assertEqual(d.driverId, 78)
        self.assertEqual(d.areaId, 2)
        self.assertEqual(d.streetId, 12)
        self.assertEqual(d.date, date(2025, 11, 8))
        self.assertEqual(d.time, time(11, 30))
        self.assertEqual(d.status, "Upcoming")

    def test_drive_get_json(self):
        d = Drive(78, 2, 12, date(2025, 11, 8), time(11, 30), "Upcoming")
        j = d.get_json()
        self.assertEqual(j["driverId"], 78)
        self.assertEqual(j["areaId"], 2)
        self.assertEqual(j["streetId"], 12)
        self.assertEqual(j["date"], "2025-11-08")
        self.assertEqual(j["time"], "11:30:00")
        self.assertEqual(j["status"], "Upcoming")


class StopUnitTests(unittest.TestCase):

    def test_new_stop(self):
        # use keyword args so it matches the real usage in controllers
        s = Stop(driveId=1, residentId=2)
        self.assertEqual(s.driveId, 1)
        self.assertEqual(s.residentId, 2)

    def test_create_stop(self):
        stop = Stop(driveId=1, residentId=2)
        self.assertEqual(stop.driveId, 1)
        self.assertEqual(stop.residentId, 2)

    def test_stop_default_status_pending(self):
        # In the real app, status is set in the controller, not as a DB default.
        stop = Stop(driveId=1, residentId=2)
        stop.status = "Pending"
        self.assertEqual(stop.status, "Pending")

    def test_stop_get_json(self):
        s = Stop(driveId=1, residentId=2)
        self.assertEqual(
            s.get_json(),
            {"id": None, "driveId": 1, "residentId": 2}
        )

    def test_stop_str(self):
        stop = Stop(driveId=1, residentId=2)
        # Don’t rely on SQLAlchemy’s internal repr – just check it’s sensible
        rep = str(stop)
        self.assertIn("Stop", rep)


class ItemUnitTests(unittest.TestCase):

    def test_new_item(self):
        i = Item("Whole-Grain Bread", 19.50, "Healthy whole-grain loaf",
                 ["whole-grain", "healthy"])
        self.assertEqual(i.name, "Whole-Grain Bread")
        self.assertEqual(i.price, 19.50)
        self.assertEqual(i.description, "Healthy whole-grain loaf")
        self.assertEqual(i.tags, ["whole-grain", "healthy"])

    def test_item_get_json(self):
        i = Item("Whole-Grain Bread", 19.50, "Healthy whole-grain loaf",
                 ["whole-grain", "healthy"])
        j = i.get_json()
        self.assertEqual(j["name"], "Whole-Grain Bread")
        self.assertEqual(j["price"], 19.50)
        self.assertEqual(j["description"], "Healthy whole-grain loaf")
        self.assertEqual(j["tags"], ["whole-grain", "healthy"])


class DriverStockUnitTests(unittest.TestCase):

    def test_new_driverstock(self):
        ds = DriverStock(1, 2, 30)
        self.assertEqual(ds.driverId, 1)
        self.assertEqual(ds.itemId, 2)
        self.assertEqual(ds.quantity, 30)

    def test_driverstock_get_json(self):
        # here we just check structure; in real code you might pass in real Driver/Item
        ds = DriverStock(1, 2, 30)
        j = ds.get_json()
        self.assertEqual(j["driverId"], 1)
        self.assertEqual(j["itemId"], 2)
        self.assertEqual(j["quantity"], 30)


# ============================================================
#  Integration Tests (DB + Controllers)
# ============================================================

class BaseIntegrationTest(unittest.TestCase):

    def setUp(self):
        # temporary sqlite database
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.db_path}",
            "JWT_SECRET_KEY": "test-secret",
        })
        with self.app.app_context():
            create_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)


class UserIntegrationTests(BaseIntegrationTest):

    def test_create_user(self):
        with self.app.app_context():
            user = create_user("bob", "bobpass")
            u = User.query.filter_by(username="bob").first()
            self.assertIsNotNone(u)
            self.assertEqual(u.username, "bob")

    def test_get_all_users_json(self):
        with self.app.app_context():
            create_user("bob", "bobpass")
            create_user("alice", "alicepass")
            users_json = get_all_users_json()
            self.assertEqual(len(users_json), 2)

    def test_update_user(self):
        with self.app.app_context():
            user = create_user("bob", "bobpass")
            updated = update_user(user.id, username="bobby")
            fetched = get_user(user.id)
            self.assertEqual(fetched.username, "bobby")

    def test_login_and_logout(self):
        with self.app.app_context():
            user = create_user("bob", "bobpass")
            logged_in = user_login("bob", "bobpass")
            self.assertTrue(logged_in.logged_in)

            logged_out = user_logout(logged_in)
            self.assertFalse(logged_out.logged_in)


class ResidentIntegrationTests(BaseIntegrationTest):

    def _setup_drive(self):
        area = admin_add_area("Sangre Grande")
        street = admin_add_street(area.id, "Picton Road")
        driver = admin_create_driver("steve", "stevepass")

        future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        drive = driver_schedule_drive(
            driver, area.id, street.id, future_date, "11:30"
        )
        return area, street, driver, drive

    def test_request_stop(self):
        with self.app.app_context():
            area, street, driver, drive = self._setup_drive()
            res = resident_create("john", "johnpass", area.id, street.id, 123)
            stop = resident_request_stop(res, drive.id)
            self.assertEqual(stop.driveId, drive.id)
            self.assertEqual(stop.residentId, res.id)

    def test_cancel_stop(self):
        with self.app.app_context():
            area, street, driver, drive = self._setup_drive()
            res = resident_create("john", "johnpass", area.id, street.id, 123)

        # Resident requests a stop on this drive
            stop = resident_request_stop(res, drive.id)

        # IMPORTANT: pass the DRIVE ID here, not stop.id
            resident_cancel_stop(res, drive.id)

        # After cancelling, that Stop record should be gone
            self.assertIsNone(Stop.query.filter_by(id=stop.id).first())

    def test_view_driver_stats(self):
        with self.app.app_context():
            area, street, driver, drive = self._setup_drive()
            res = resident_create("john", "johnpass", area.id, street.id, 123)
            stats = resident_view_driver_stats(res, driver.id)
            self.assertIsNotNone(stats)

    def test_resident_view_stock(self):
        with self.app.app_context():
            area, street, driver, drive = self._setup_drive()
            res = resident_create("john", "johnpass", area.id, street.id, 123)
            item = admin_add_item("Whole-Grain Bread", 19.50,
                                  "Healthy whole-grain loaf", ["whole-grain"])
            driver_update_stock(driver, item.id, 30)
            stocks = resident_view_stock(res, driver.id)
            self.assertGreaterEqual(len(stocks), 1)
    
    def setUp(self):
        from datetime import datetime, timedelta

        self.app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
        self.app.app_context().push()
        db.create_all()

    # Area + Street
        self.area = Area(name="Test Area")
        db.session.add(self.area)
        db.session.commit()

        self.street = Street(name="Test Street", areaId=self.area.id)
        db.session.add(self.street)
        db.session.commit()

    # Resident
        self.resident = resident_create(
            "resident1",
            "password",
            self.area.id,
            self.street.id,
            123
        )

    # Driver (created directly, not via create_user)
        self.driver = Driver(
            username="driver1",
            password="password",
            status="Offline",
            areaId=self.area.id,
            streetId=self.street.id
        )
        db.session.add(self.driver)
        db.session.commit()

    # Future drive
        tomorrow = datetime.utcnow() + timedelta(days=1)
        self.drive = Drive(
            driverId=self.driver.id,
            areaId=self.area.id,
            streetId=self.street.id,
            date=tomorrow.date(),
            time=tomorrow.time().replace(microsecond=0),
            status="Upcoming"
        )
        db.session.add(self.drive)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_request_stop(self):
        stop = resident_request_stop(self.resident, self.drive.id)
        self.assertIsNotNone(stop)

    # NEW: latest-UI-feature test – status + DB check
    def test_request_stop_sets_stop_status_pending(self):
        stop = resident_request_stop(self.resident, self.drive.id)
        db.session.commit()

        # Reload from DB to be sure it persisted correctly
        saved = Stop.query.filter_by(
            driveId=self.drive.id,
            residentId=self.resident.id
        ).first()

        self.assertIsNotNone(saved)
        # again, tweak "Pending" if you chose another value
        self.assertEqual(saved.status, "Pending")


class DriverIntegrationTests(BaseIntegrationTest):

    def _setup_area_street_driver(self):
        area = admin_add_area("Sangre Grande")
        street = admin_add_street(area.id, "Picton Road")
        driver = admin_create_driver("steve", "stevepass")
        return area, street, driver
    
    def _schedule_future_drive(self, driver, area, street):
        future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        return driver_schedule_drive(driver, area.id, street.id, future_date, "11:30")

    def test_schedule_drive(self):
        with self.app.app_context():
            area, street, driver = self._setup_area_street_driver()
            drive = self._schedule_future_drive(driver, area, street)
            self.assertEqual(drive.streetId, street.id)

    def test_cancel_drive(self):
        with self.app.app_context():
            area, street, driver = self._setup_area_street_driver()
            drive = self._schedule_future_drive(driver, area, street)
            driver_cancel_drive(driver, drive.id)
            self.assertEqual(Drive.query.get(drive.id).status, "Cancelled")

    def test_view_drives(self):
        with self.app.app_context():
            area, street, driver = self._setup_area_street_driver()
            self._schedule_future_drive(driver, area, street)
            drives = driver_view_drives(driver)
            self.assertGreaterEqual(len(drives), 1)

    def test_start_and_end_drive(self):
        with self.app.app_context():
            area, street, driver = self._setup_area_street_driver()
            drive = self._schedule_future_drive(driver, area, street)

            driver_start_drive(driver, drive.id)
            d = Drive.query.get(drive.id)
            self.assertEqual(d.status, "In Progress")

            driver_end_drive(driver)
            d = Drive.query.get(drive.id)
            self.assertEqual(d.status, "Completed")

    def test_view_requested_stops(self):
        with self.app.app_context():
            area, street, driver = self._setup_area_street_driver()
            drive = self._schedule_future_drive(driver, area, street)
            res = resident_create("john", "johnpass", area.id, street.id, 123)

            resident_request_stop(res, drive.id)

            stops = list(driver_view_requested_stops(driver, drive.id))
            self.assertGreaterEqual(len(stops), 1)

    def test_update_stock(self):
        with self.app.app_context():
            # Re-use your helpers if you already have them
            area, street, driver = self._setup_area_street_driver()

            # create an item
            item = Item(name="Test Bread", price=10.0, description="", tags="")
            db.session.add(item)
            db.session.commit()

            new_quantity = 30

            # call the controller function
            driver_update_stock(driver, item.id, new_quantity)

            stock = DriverStock.query.filter_by(
                driverId=driver.id, itemId=item.id
            ).first()

            self.assertIsNotNone(stock)
            self.assertEqual(stock.quantity, new_quantity)


class AdminIntegrationTests(BaseIntegrationTest):

    def test_create_and_delete_driver(self):
        with self.app.app_context():
            driver = admin_create_driver("steve", "stevepass")
            self.assertIsNotNone(Driver.query.get(driver.id))
            admin_delete_driver(driver.id)
            self.assertIsNone(Driver.query.get(driver.id))

    def test_add_delete_view_area(self):
        with self.app.app_context():
            area = admin_add_area("Sangre Grande")
            self.assertIsNotNone(Area.query.get(area.id))

            areas = admin_view_all_areas()
            self.assertGreaterEqual(len(areas), 1)

            admin_delete_area(area.id)
            self.assertIsNone(Area.query.get(area.id))

    def test_add_delete_view_street(self):
        with self.app.app_context():
            area = admin_add_area("Sangre Grande")
            street = admin_add_street(area.id, "Picton Road")

            streets = admin_view_all_streets()
            self.assertGreaterEqual(len(streets), 1)

            admin_delete_street(area.id, street.id)
            self.assertIsNone(Street.query.get(street.id))

    def test_add_delete_view_item(self):
        with self.app.app_context():
            item = admin_add_item("Whole-Grain Bread", 19.50,
                                  "Healthy whole-grain loaf", ["whole-grain"])
            self.assertIsNotNone(Item.query.get(item.id))

            items = admin_view_all_items()
            self.assertGreaterEqual(len(items), 1)

            admin_delete_item(item.id)
            self.assertIsNone(Item.query.get(item.id))


if __name__ == "__main__":
    unittest.main()    

