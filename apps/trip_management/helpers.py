from apps.trip_management.config import sms_url_builder, host
from apps.trip_management.models import DeliveryMan, TripDeliveryMan
import requests

def get_salespoint_data(): pass

def get_salesperson_data(salesperson):
    salesperson_data = {
        'id' : salesperson.id,
        'name' : salesperson.name,
    }
    return salesperson_data


def get_invoice_data(invoice):
    invoice_data = {
        'id': invoice.id,
        'invoice_id': invoice.invoice_id,
        'delivery_status': invoice.delivery_status,
        'sales_point': get_salespoint_data(invoice.sales_point) if invoice.sales_point else None,
        'sales_person': get_salesperson_data(invoice.sales_person) if invoice.sales_person else None,
        'created': str(invoice.created_at),
        'estimated_delivery_date': str(invoice.estimated_delivery_date),
        'selling_date': str(invoice.selling_date),
        'customer_name': invoice.customer_name,
        'delivery_address': invoice.delivery_address,
        'customer_phone_no': invoice.customer_phone_no,
        'remarks': invoice.remarks,
        'location': [invoice.lon, invoice.lat],
    }
    return invoice_data

def get_salespoint_data(sales):
    salespoint_data = {
        'id': sales.id,
        'name': sales.name,
        'address': sales.address,
        'showroom_code': sales.showroom_code,
        # 'sales_person': sales.sales_person,
    }
    return salespoint_data


def get_deliveryman_data(deliveryman):
    deliveryman_data = {
            'id': deliveryman.id,
            'name': deliveryman.name,
            'salary' : deliveryman.salary,
            'duty_hours' : deliveryman.duty_hours,
            'driver' : {
                'id' : deliveryman.driver.id,
                'name' : deliveryman.driver.name,
            } if deliveryman.driver is not None else None
    }
    return deliveryman_data


def get_driver_data(driver):
    driver_data = {
            'id': driver.id,
            'name': driver.name,
            'address' : driver.address,
            'date_of_birth' :driver.date_of_birth,
            'license_issue_date' :driver.license_issue_date,
            'license_expiry_date' :driver.license_expiry_date,
            'license_number' :driver.license_number,
            'phone_no' :driver.phone_no,
            'salary' : driver.salary,
            'duty_hours' : driver.duty_hours,
            'note' :driver.note,
    }
    driver_data['deliverymans'] = []
    deliverymans = DeliveryMan.objects.filter(driver_id=driver.id)
    if deliverymans.exists():
        for deliveryman in deliverymans:
            driver_data['deliverymans'].append(get_deliveryman_data(deliveryman))
    return driver_data


def get_trip_deliveryman(trip_deliveryman):
    trip_deliveryman_data = {
        'id' : trip_deliveryman.id,
        'trip_info_id' : trip_deliveryman.trip_info.id,
        'deliveryman' : get_deliveryman_data(trip_deliveryman.deliveryman)
    }
    return trip_deliveryman_data


def get_vehicle_data(vehicle):
    vehicle_data = {
        'id': vehicle.id,
        'imei' :vehicle.imei,
        'license_plate' :vehicle.license_plate,
        'title' :vehicle.title,
        'driver' : get_driver_data(vehicle.driver) if vehicle.driver is not None else None,
        'purchase_date' :vehicle.purchase_date,
        'build_year' :vehicle.build_year,
        'vehicle_icon' :vehicle.vehicle_icon,
        'brand' :vehicle.brand,
        'model_number' :vehicle.model_number,
        'chassis_number' :vehicle.chassis_number,
        'engine_number' :vehicle.engine_number,
        'registration_number' :vehicle.registration_number,
        'color' :vehicle.color,
        'body_type' :vehicle.body_type,
        'fuel_capacity' :vehicle.fuel_capacity,
        'kpl' :vehicle.kpl,
        'fuel_reading_status' :vehicle.fuel_reading_status,
        'formula' :vehicle.formula,
        'refuel_percentage_threshold' :vehicle.refuel_percentage_threshold,
        'refuel_ltr_threshold' :vehicle.refuel_ltr_threshold,
        'leakage_percentage_threshold' :vehicle.leakage_percentage_threshold,
        'leakage_ltr_threshold' :vehicle.leakage_ltr_threshold,
        'fuel_speed_threshold' :vehicle.fuel_speed_threshold,
        'fuel_data_delay' :vehicle.fuel_data_delay,
        'height' :vehicle.height,
        'weight' :vehicle.weight,
        'width' :vehicle.width,
        'address' :vehicle.address,
    }
    return vehicle_data


def get_warehouse_data(warehouse):
    warehouse_data = {
        'id': warehouse.id,
        'name': warehouse.name,
        'address': warehouse.address,
        'location': [warehouse.lon, warehouse.lat],
    }
    return warehouse_data


def get_tripinfo_data(trip):
    tripinfo_data = {
        'id': trip.id,
        'driver': get_driver_data(trip.driver),
        'vehicle': get_vehicle_data(trip.vehicle),
        'warehouse': get_warehouse_data(trip.warehouse),
        'trip_status': trip.trip_status,
    }
    dlm = TripDeliveryMan.objects.filter(trip_info_id = trip.id)
    if dlm.exists():
         tripinfo_data['deliverymans'] = []
         for man in dlm:
             tripinfo_data['deliverymans'].append(get_deliveryman_data(man.deliveryman))
    return tripinfo_data


def get_destionation_data(destination):
    destionation_data = {
        'id' : destination.id,
        'trip_info_id': destination.trip_info.id,
        'invoice' : get_invoice_data(destination.invoice),
        'sms_status' : 'OK' if destination.sms_status==200 else 'FAILED', 
        'location': [destination.invoice.lon, destination.invoice.lat],
        'sequence': destination.sequence,
    }
    return destionation_data


def trip_sms_sender(number, invoice_id, driver_name, driver_contact):
    link = host+"schedules/tracking/"+str(invoice_id)
    msg = "Hi, Your order: "+invoice_id+" has been scheduled for delivery."\
          +" Carrier: "+ driver_name + ", Contact:"+driver_contact\
          +". Track your item here " + link
    sms_url = sms_url_builder(number, msg)
    response = requests.get(sms_url)
    return response
