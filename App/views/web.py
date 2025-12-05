from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import (
    set_access_cookies,
    unset_jwt_cookies,
    jwt_required,
    get_jwt_identity
)
import datetime
from collections import defaultdict
from App.database import db
from App.controllers.driver import (
    driver_schedule_drive,
    driver_cancel_drive,
    driver_view_drives,
    driver_start_drive,
    driver_end_drive,
    driver_view_requested_stops,
    driver_approve_stop,      
    driver_reject_stop,
    driver_view_stock,
    driver_update_stock
)
from App.controllers.resident import (
    resident_view_inbox,
    resident_cancel_stop,
    resident_request_stop,
)
from App.models import Area, Street, Driver, Resident, Item, User, Admin, Drive, Stop, DriverStock
from App.controllers.admin import admin_create_driver
from App.controllers.resident import resident_create, resident_view_inbox
from App.controllers import login as login_controller, get_user
from App.controllers.user import user_login, user_logout
from App.models import Area, Street, Driver, Resident, Item

web_views = Blueprint("web_views", __name__, template_folder="../templates")

# HTML Login

@web_views.route("/web/login", methods=["GET", "POST"])
def login():
    
    if request.method == "GET":
        return render_template("login.html")

   
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Please enter both username and password.", "error")
        return render_template("login.html")

    try:
        user = user_login(username, password)
    except ValueError:
        flash("Invalid username or password.", "error")
        return render_template("login.html")

    token = login_controller(username, password)
    if not token:
        flash("Unexpected error creating session.", "error")
        return render_template("login.html")

    resp = redirect(url_for("web_views.dashboard"))
    set_access_cookies(resp, token)
    flash("Login successful.", "success")
    return resp


# Logout

@web_views.route("/web/logout")
@jwt_required(optional=True)
def logout():
    identity = get_jwt_identity()
    if identity:
        user = get_user(identity)
        if user:
            
            user_logout(user)

    resp = redirect(url_for("web_views.login"))
    unset_jwt_cookies(resp)
    flash("Logged out.", "success")
    return resp


# Role-based dashboard router

@web_views.route("/dashboard")
@jwt_required()
def dashboard():
    uid = get_jwt_identity()
    user = get_user(uid)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("web_views.login"))

    if user.type == "Admin":
        return redirect(url_for("web_views.admin_dashboard"))
    elif user.type == "Driver":
        return redirect(url_for("web_views.driver_dashboard"))
    elif user.type == "Resident":
        return redirect(url_for("web_views.resident_dashboard"))

    flash("Unknown user type.", "error")
    return redirect(url_for("web_views.login"))


# Simple HTML dashboards for each role

@web_views.route("/admin/dashboard")
@jwt_required()
def admin_dashboard():
    uid = get_jwt_identity()
    user = get_user(uid)
    if not user or user.type != "Admin":
        flash("Unauthorized.", "error")
        return redirect(url_for("web_views.login"))

    areas = Area.query.all()
    streets = Street.query.all()
    items = Item.query.all()
    drivers = Driver.query.all()
    residents = Resident.query.all()

    return render_template(
        "admin/dashboard.html",
        current_user=user,
        areas=areas,
        streets=streets,
        items=items,
        drivers=drivers,
        residents=residents,
    )

@web_views.route("/admin/create-driver", methods=["POST"])
@jwt_required()
def admin_create_driver_view():
    uid = get_jwt_identity()
    admin = get_user(uid)
    if not admin or admin.type != "Admin":
        flash("Unauthorized.", "error")
        return redirect(url_for("web_views.login"))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Username and password are required.", "error")
        return redirect(url_for("web_views.admin_dashboard"))

    try:
        driver = admin_create_driver(username, password)
        flash(f"Driver '{driver.username}' created successfully.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("web_views.admin_dashboard"))

@web_views.route("/admin/create-resident", methods=["POST"])
@jwt_required()
def admin_create_resident_view():
    uid = get_jwt_identity()
    admin = get_user(uid)
    if not admin or admin.type != "Admin":
        flash("Unauthorized.", "error")
        return redirect(url_for("web_views.login"))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    area_id = request.form.get("area_id")
    street_id = request.form.get("street_id")
    house_number = request.form.get("house_number")

    if not (username and password and area_id and street_id and house_number):
        flash("All resident fields are required.", "error")
        return redirect(url_for("web_views.admin_dashboard"))

    try:
        area_id = int(area_id)
        street_id = int(street_id)
        house_number = int(house_number)
    except ValueError:
        flash("Area, street and house number must be valid integers.", "error")
        return redirect(url_for("web_views.admin_dashboard"))

    try:
        resident = resident_create(username, password, area_id, street_id, house_number)
        flash(
            f"Resident '{resident.username}' created at #{resident.houseNumber}.",
            "success",
        )
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("web_views.admin_dashboard"))

@web_views.route("/driver/dashboard", methods=["GET", "POST"])
@jwt_required()
def driver_dashboard():
    uid = get_jwt_identity()
    driver = get_user(uid)

    if not driver or driver.type != "Driver":
        flash("Unauthorized.", "error")
        return redirect(url_for("web_views.login"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "schedule_drive":
            date_str = request.form.get("date_str", "").strip()
            time_str = request.form.get("time_str", "").strip()
            area_id = request.form.get("area_id", type=int)
            street_id = request.form.get("street_id", type=int)

            if not date_str or not time_str or not area_id or not street_id:
                flash("Please fill in date, time, area and street.", "error")
            else:
                try:
                    new_drive = driver_schedule_drive(
                        driver,
                        area_id,
                        street_id,
                        date_str,
                        time_str
                    )

                    residents = Resident.query.filter_by(
                        areaId=area_id,
                        streetId=street_id
                    ).all()

                    for r in residents:
                        r.receive_notif(
                            f"[Drive #{new_drive.id}] New bread van drive by "
                            f"{driver.username} scheduled to {r.street.name}, {r.area.name} "
                            f"on {date_str} at {time_str}. "
                            f"Login to request a stop and view the menu."
                        )

                    db.session.commit()
                    flash("Drive scheduled and residents notified.", "success")

                except ValueError as e:
                    flash(str(e), "error")

        elif action == "approve_stop":
            stop_id = request.form.get("stop_id", type=int)
            stop = Stop.query.get(stop_id)

            if not stop or not stop.drive or stop.drive.driverId != driver.id:
                flash("Could not approve that stop.", "error")
            else:
                stop.status = "Approved"
                stop.resident.receive_notif(
                    f"Your request for drive #{stop.driveId} has been approved "
                    f"by {driver.username}."
                )
                db.session.commit()
                flash("Stop approved.", "success")

        elif action == "reject_stop":
            stop_id = request.form.get("stop_id", type=int)
            stop = Stop.query.get(stop_id)

            if not stop or not stop.drive or stop.drive.driverId != driver.id:
                flash("Could not reject that stop.", "error")
            else:
                stop.status = "Rejected"
                stop.resident.receive_notif(
                    f"Your request for drive #{stop.driveId} was rejected by "
                    f"{driver.username}."
                )
                db.session.commit()
                flash("Stop rejected.", "success")

        elif action == "send_update":
            resident_id = request.form.get("resident_id", type=int)
            drive_id = request.form.get("drive_id", type=int)
            eta_text = request.form.get("eta_text", "").strip()
            status_text = request.form.get("status_text", "").strip()

            if not (eta_text or status_text):
                flash("Please enter an ETA or status message.", "error")
            else:
                res = Resident.query.get(resident_id)
                drv = Drive.query.get(drive_id)

                if not res or not drv or drv.driverId != driver.id:
                    flash("Could not send update for that stop.", "error")
                else:
                    parts = []
                    if eta_text:
                        parts.append(f"ETA: {eta_text}")
                    if status_text:
                        parts.append(f"Status: {status_text}")

                    msg = (
                        f"Update for drive #{drv.id} to "
                        f"{res.street.name}, {res.area.name}: "
                        + " | ".join(parts)
                    )

                    res.receive_notif(msg)
                    db.session.commit()
                    flash("Update sent to resident.", "success")

        elif action == "add_stock":
            name = request.form.get("item_name", "").strip()
            price = request.form.get("item_price", type=float)
            quantity = request.form.get("item_quantity", type=int)

            if not name or quantity is None:
                flash("Please provide item name and quantity.", "error")
            else:
                item = Item.query.filter_by(name=name).first()
                if not item:
                    item = Item(
                        name=name,
                        price=price or 0.0,
                        description="Bakery item",
                        tags=""
                    )
                    db.session.add(item)
                    db.session.flush()  

                stock = DriverStock.query.filter_by(
                    driverId=driver.id,
                    itemId=item.id
                ).first()

                if stock:
                    stock.quantity = quantity
                else:
                    stock = DriverStock(
                        driverId=driver.id,
                        itemId=item.id,
                        quantity=quantity
                    )
                    db.session.add(stock)

                if price is not None:
                    item.price = price

                db.session.commit()
                flash("Menu updated.", "success")

        elif action == "delete_stock":
            stock_id = request.form.get("stock_id", type=int)
            stock = DriverStock.query.get(stock_id)
            if not stock or stock.driverId != driver.id:
                flash("Could not delete that item.", "error")
            else:
                db.session.delete(stock)
                db.session.commit()
                flash("Item removed from your menu.", "success")

    areas = Area.query.order_by(Area.name).all()
    streets = Street.query.order_by(Street.name).all()

    all_drives = driver_view_drives(driver)
    drives = [
        d for d in all_drives
        if d.status in ("Upcoming", "In Progress")
    ]

    stops_by_drive = defaultdict(list)
    for d in drives:
        for st in driver_view_requested_stops(driver, d.id):
            stops_by_drive[d.id].append(st)

    stocks = driver_view_stock(driver)

    return render_template(
        "driver/dashboard.html",
        driver=driver,
        areas=areas,
        streets=streets,
        drives=drives,
        stops_by_drive=stops_by_drive,
        stocks=stocks,
    )
