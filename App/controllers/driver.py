from App.models import Driver, Drive, Street, Item, DriverStock, Resident, Stop
from App.database import db
from datetime import datetime, timedelta

def driver_schedule_drive(driver, area_id, street_id, date_str, time_str):
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        raise ValueError("Invalid date or time format. Use YYYY-MM-DD and HH:MM.")

    scheduled_datetime = datetime.combine(date, time)

    if scheduled_datetime < datetime.now():
        raise ValueError("Cannot schedule a drive in the past.")

    one_year_later = datetime.now() + timedelta(days=60)
    if scheduled_datetime > one_year_later:
        raise ValueError("Cannot schedule a drive more than 60 days in advance.")

    existing_drive = Drive.query.filter_by(
        areaId=area_id,
        streetId=street_id,
        date=date
    ).first()

    new_drive = driver.schedule_drive(area_id, street_id, date_str, time_str)

    residents = Resident.query.filter_by(
        areaId=area_id,
        streetId=street_id
    ).all()

    for r in residents:
        r.receive_notif(
            f"SCHEDULED>> Drive {new_drive.id} by Driver {driver.username} "
            f"on {new_drive.date} at {new_drive.time}"
        )

    db.session.commit()
    return new_drive

def driver_cancel_drive(driver, drive_id):
    return driver.cancel_drive(drive_id)

def driver_view_drives(driver):
    return [d for d in driver.view_drives() if d.status in ("Upcoming", "In Progress")]

def driver_start_drive(driver, drive_id):
    current_drive = Drive.query.filter_by(driverId=driver.id, status="In Progress").first()
    if current_drive:
        raise ValueError(f"You are already on drive {current_drive.id}.")
    drive = Drive.query.filter_by(driverId=driver.id, id=drive_id, status="Upcoming").first()
    if not drive:
        raise ValueError("Drive not found or cannot be started.")
    return driver.start_drive(drive_id)

def driver_end_drive(driver):
    current_drive = Drive.query.filter_by(driverId=driver.id, status="In Progress").first()
    if not current_drive:
        raise ValueError("No drive in progress.")
    return driver.end_drive(current_drive.id)

def driver_view_requested_stops(driver, drive_id):
    stops = driver.view_requested_stops(drive_id)
    if not stops:
        return []
    return stops

def driver_update_stock(driver, item_id, quantity):
    item =  Item.query.get(item_id)
    if not item:
        raise ValueError("Invalid item ID.")
    stock =  DriverStock.query.filter_by(driverId=driver.id, itemId=item_id).first()
    if stock:
        stock.quantity = quantity
    else:
        stock = DriverStock(driverId=driver.id, itemId=item_id, quantity=quantity)
        db.session.add(stock)
    db.session.commit()
    return stock

def driver_view_stock(driver):
    stocks = DriverStock.query.filter_by(driverId=driver.id).all() 
    return stocks
    
def driver_approve_stop(driver, stop_id, eta=None, status_msg=None):
    stop = Stop.query.get(stop_id)
    if not stop:
        raise ValueError("Stop not found.")

    drive = stop.drive
    if drive.driverId != driver.id:
        raise ValueError("Unauthorized for this stop.")

    stop.status = "Subscribed"
    if eta:
        stop.eta = eta
    if status_msg:
        stop.driver_status_msg = status_msg

    resident = stop.resident
    resident.receive_notif(
        f"APPROVED>> Your stop request for drive {drive.id} "
        f"has been approved. ETA: {stop.eta or 'N/A'}, Status: {stop.driver_status_msg or 'Subscribed'}"
    )

    db.session.commit()
    return stop


def driver_reject_stop(driver, stop_id, reason=None):
    stop = Stop.query.get(stop_id)
    if not stop:
        raise ValueError("Stop not found.")

    drive = stop.drive
    if drive.driverId != driver.id:
        raise ValueError("Unauthorized for this stop.")

    stop.status = "Rejected"
    if reason:
        stop.driver_status_msg = reason

    resident = stop.resident
    txt_reason = f" Reason: {reason}" if reason else ""
    resident.receive_notif(
        f"REJECTED>> Your stop request for drive {drive.id} was rejected.{txt_reason}"
    )

    db.session.commit()
    return stop