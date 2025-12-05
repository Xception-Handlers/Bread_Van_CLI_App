from App.models import Resident, Stop, Drive, Area, Street, DriverStock
from App.database import db


def resident_create(username, password, area_id, street_id, house_number):
    resident = Resident(
        username=username,
        password=password,
        areaId=area_id,
        streetId=street_id,
        houseNumber=house_number
    )
    db.session.add(resident)
    db.session.commit()
    return resident

def resident_request_stop(resident, drive_id):
    drive = Drive.query.get(drive_id)
    if not drive or drive.status != "Upcoming":
        raise ValueError("Drive not available for requests.")

  
    existing = Stop.query.filter_by(
        residentId=resident.id,
        driveId=drive.id
    ).first()
    if existing:
        raise ValueError("You already requested a stop for this drive.")

    
    stop = Stop(
        residentId=resident.id,
        driveId=drive.id,
        status="Pending"
    )
    db.session.add(stop)

    
    if hasattr(resident, "receive_notif"):
        time_part = (
            drive.time.strftime('%H:%M')
            if getattr(drive, "time", None) is not None else ""
        )
        resident.receive_notif(
            f"You requested a stop on drive #{drive.id} to "
            f"{drive.street.name}, {drive.area.name} at {time_part}."
        )

    db.session.commit()
    return stop

def resident_cancel_stop(resident, drive_id):
    """
    Resident cancels their stop for a drive.
    - Uses the existing resident.cancel_stop(stop.id) so core behaviour & tests remain.
    - Adds notifications to BOTH resident inbox and driver inbox.
    """
    stop = Stop.query.filter_by(driveId=drive_id, residentId=resident.id).first()
    if not stop:
        raise ValueError("No stop requested for this drive.")

    drive = Drive.query.get(drive_id)

    
    if drive and getattr(drive, "driver", None) and hasattr(drive.driver, "receive_notif"):
        time_part = (
            drive.time.strftime('%H:%M')
            if getattr(drive, "time", None) is not None else ""
        )
        drive.driver.receive_notif(
            f"Resident {resident.username} cancelled their stop request "
            f"for drive #{drive.id} to {drive.street.name}, {drive.area.name} "
            f"at {time_part}."
        )

    
    if hasattr(resident, "receive_notif"):
        time_part = (
            drive.time.strftime('%H:%M')
            if drive and getattr(drive, "time", None) is not None else ""
        )
        resident.receive_notif(
            f"You cancelled your stop request for drive #{drive.id} "
            f"to {drive.street.name}, {drive.area.name} at {time_part}."
        )

   
    resident.cancel_stop(stop.id)

    
    db.session.commit()

    return stop

def resident_view_inbox(resident):
    return resident.view_inbox()

def resident_view_driver_stats(resident, driver_id):
    driver = resident.view_driver_stats(driver_id)
    if not driver:
        raise ValueError("Driver not found.")
    return driver

def resident_view_stock(resident, driver_id):
    driver = resident.view_driver_stats(driver_id)
    if not driver:
        raise ValueError("Driver not found.")
    stocks = DriverStock.query.filter_by(driverId=driver_id).all()
    return stocks