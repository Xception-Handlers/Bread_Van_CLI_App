from datetime import datetime, timedelta

from App.database import create_db, db
from App.models import User, Admin, Area, Street, Driver, Resident, Drive
from App.controllers.driver import driver_schedule_drive
from App.controllers.resident import resident_request_stop

import os
from flask import current_app

# def initialize():
#     db.drop_all()
#     db.create_all()

#     #Creating Admin
#     admin = Admin(username="admin", password="adminpass")
#     db.session.add(admin)
#     db.session.commit()

#     #Creating Areas and Streets
#     area1 = Area(name='St. Augustine')
#     db.session.add(area1)
#     db.session.commit()

#     street11 = Street(name="Gordon Street", areaId=area1.id)
#     street12 = Street(name="Warner Street", areaId=area1.id)
#     street13 = Street(name="College Road", areaId=area1.id)
#     db.session.add_all([street11, street12, street13])
#     db.session.commit()

#     area2 = Area(name='Tunapuna')
#     db.session.add(area2)
#     db.session.commit()

#     street21 = Street(name="Fairly Street", areaId=area2.id)
#     street22 = Street(name="Saint John Road", areaId=area2.id)
#     db.session.add_all([street21, street22])
#     db.session.commit()

#     area3 = Area(name='San Juan')
#     db.session.add(area3)
#     db.session.commit()

#     #Creating Drivers
#     driver1 = Driver(username="bob",
#                      password="bobpass",
#                      status="Offline",
#                      areaId=area1.id,
#                      streetId=street11.id)
#     driver2 = Driver(username="mary",
#                      password="marypass",
#                      status="Available",
#                      areaId=area2.id,
#                      streetId=None)
#     db.session.add_all([driver1, driver2])
#     db.session.commit()

#     #Creating Residents and Stops
#     resident1 = Resident(username="alice",
#                          password="alicepass",
#                          areaId=area1.id,
#                          streetId=street12.id,
#                          houseNumber=48)
#     resident2 = Resident(username="jane",
#                          password="janepass",
#                          areaId=area1.id,
#                          streetId=street12.id,
#                          houseNumber=50)
#     resident3 = Resident(username="john",
#                          password="johnpass",
#                          areaId=area2.id,
#                          streetId=street21.id,
#                          houseNumber=13)
#     db.session.add_all([resident1, resident2, resident3])
#     db.session.commit()

#     #Creating Drives and Stops
#     driver2.schedule_drive(area1.id, street12.id, "2025-10-26", "10:00")
#     db.session.commit()
                     
#     resident2.request_stop(0)
#     db.session.commit()

from datetime import datetime, timedelta

from App.database import create_db, db
from App.models import User, Admin, Area, Street, Driver, Resident, Drive
from App.controllers.driver import driver_schedule_drive
from App.controllers.resident import resident_request_stop


# def initialize():
#   
#     create_db()  # this should call db.create_all() inside

#     admin = db.session.execute(
#         db.select(User).filter_by(username="admin")
#     ).scalar_one_or_none()
#     if admin is None:
#         admin = Admin(username="admin", password="adminpass")
#         db.session.add(admin)
#         db.session.commit()

# 
#     if Area.query.count() == 0:
#         area1 = Area(name="St Augustine")
#         area2 = Area(name="Tunapuna")
#         area3 = Area(name="San Juan")
#         db.session.add_all([area1, area2, area3])
#         db.session.flush()  # get IDs without full commit yet

#         
#         streets = [
#             Street(name="Gordon Street", areaId=area1.id),
#             Street(name="Warner Street", areaId=area1.id),
#             Street(name="College Road", areaId=area1.id),
#             Street(name="Fairly Street", areaId=area2.id),
#             Street(name="St John Road", areaId=area2.id),
#         ]
#         db.session.add_all(streets)
#         db.session.commit()

#     
#     area1 = Area.query.filter_by(name="St Augustine").first()
#     area2 = Area.query.filter_by(name="Tunapuna").first()
#    
#     gordon = Street.query.filter_by(name="Gordon Street").first()
#     warner = Street.query.filter_by(name="Warner Street").first()
#     fairly = Street.query.filter_by(name="Fairly Street").first()

#    
#     bob = db.session.execute(
#         db.select(User).filter_by(username="bob")
#     ).scalar_one_or_none()
#     if bob is None:
#         driver1 = Driver(
#             username="bob",
#             password="bobpass",
#             status="Offline",
#             areaId=area1.id if area1 else None,
#             streetId=gordon.id if gordon else None,
#         )
#         driver2 = Driver(
#             username="mary",
#             password="marypass",
#             status="Available",
#             areaId=area2.id if area2 else None,
#             streetId=None,
#         )
#         db.session.add_all([driver1, driver2])
#         db.session.commit()

#  
#     driver1 = Driver.query.join(User).filter(User.username == "bob").first()
#     driver2 = Driver.query.join(User).filter(User.username == "mary").first()

#     
#     alice = db.session.execute(
#         db.select(User).filter_by(username="alice")
#     ).scalar_one_or_none()

#     if alice is None:
#         resident1 = Resident(
#             username="alice",
#             password="alicepass",
#             areaId=area1.id if area1 else None,
#             streetId=warner.id if warner else None,
#             houseNumber=48,
#         )
#         resident2 = Resident(
#             username="jane",
#             password="janepass",
#             areaId=area1.id if area1 else None,
#             streetId=warner.id if warner else None,
#             houseNumber=50,
#         )
#         resident3 = Resident(
#             username="john",
#             password="johnpass",
#             areaId=area2.id if area2 else None,
#             streetId=fairly.id if fairly else None,
#             houseNumber=13,
#         )
#         db.session.add_all([resident1, resident2, resident3])
#         db.session.commit()

#     resident2 = Resident.query.join(User).filter(User.username == "jane").first()

#  
#     if Drive.query.count() == 0 and driver2 and area1 and warner and resident2:
#         future_date = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

#         
#         new_drive = driver_schedule_drive(
#             driver2,
#             area1.id,
#             warner.id,
#             future_date,
#             "10:00",
#         )

#         resident_request_stop(resident2, new_drive.id)
#         db.session.commit()

def initialize():
   
    app = current_app
    app.logger.info("Running initialize()")

   
    create_db()

   
    admin = Admin.query.filter_by(username="admin").first()
    if not admin:
        app.logger.info("Creating default admin user 'admin'")
        admin = Admin(username="admin", password="adminpass")
        db.session.add(admin)
        db.session.commit()

    
    if Area.query.count() == 0:
        app.logger.info("Seeding default areas & streets")

        
        st_aug = Area(name="St. Augustine")
        tunapuna = Area(name="Tunapuna")
        san_juan = Area(name="San Juan")

        db.session.add_all([st_aug, tunapuna, san_juan])
        db.session.flush()  

       
        streets = [
            Street(name="Gordon Street", areaId=st_aug.id),
            Street(name="Warner Street", areaId=st_aug.id),
            Street(name="College Road", areaId=st_aug.id),

            Street(name="Fairly Street", areaId=tunapuna.id),
            Street(name="Saint John Road", areaId=tunapuna.id),
        ]

        db.session.add_all(streets)
        db.session.commit()

    app.logger.info("initialize() completed successfully")

def seed_demo_areas_and_streets():
    
    if os.getenv("SKIP_DEMO_SEED") == "1":
        current_app.logger.info("Skipping demo area/street seed via SKIP_DEMO_SEED")
        return

    try:
        
        demo_areas = [
            "Unassigned",
            "Curepe/St Aug",
            "San Juan",
            "Sangre Grande",
            
        ]

        name_to_area = {}

        for name in demo_areas:
            area = Area.query.filter_by(name=name).first()
            if not area:
                area = Area(name=name)
                db.session.add(area)
            name_to_area[name] = area

        db.session.flush()

        
        demo_streets = [
            ("Main Road", "Curepe/St Aug"),
            ("St Aug Circ", "Curepe/St Aug"),  
            ("High St", "San Juan"),
           
        ]

        for street_name, area_name in demo_streets:
            area = name_to_area.get(area_name)
            if not area:
                continue  

            exists = Street.query.filter_by(
                name=street_name,
                areaId=area.id
            ).first()

            if not exists:
                s = Street(name=street_name, areaId=area.id)
                db.session.add(s)

        db.session.commit()
        current_app.logger.info("Demo Areas/Streets seeded successfully")

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error seeding demo Areas/Streets: %s", e)