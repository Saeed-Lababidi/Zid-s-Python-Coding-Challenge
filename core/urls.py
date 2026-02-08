"""
URL configuration for core app.
"""
from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    # Health
    # Health
    path("health/", views.health_check, name="health"),
    path("health/<str:subpath>/", views.health_check, name="health-subpath"),

    # Couriers
    path("couriers/", views.list_couriers, name="list-couriers"),
    path("couriers/<str:provider>/", views.get_courier, name="get-courier"),

    # Shipments
    path("shipments/", views.create_shipment, name="create-shipment"),
    path("shipments/<str:waybill_number>/", views.get_shipment, name="get-shipment"),
    path("shipments/<str:waybill_number>/track/", views.track_shipment, name="track-shipment"),
    path("shipments/<str:waybill_number>/label/", views.print_label, name="print-label"),
    path("shipments/<str:waybill_number>/cancel/", views.cancel_shipment, name="cancel-shipment"),
]
