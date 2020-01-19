import json
import math
import requests as req
from flask import Flask, request
from flask_json import FlaskJSON, JsonError, json_response, as_json
from math import sin, cos, sqrt, atan2, radians

auth = "db37117c-679d-41ae-b7cc-2c010daea9ed"
app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route("/pairings/")
def get_pairings():
    orders = get_orders()
    riders = get_riders()

    pairs = pairings(orders[0:10], riders[0:10])
    print("Sending: ")
    if len(pairs) < 10:
        for pair in pairs:
            print(pair)
    else:
        for pair in pairs[0:10]:
            print(pair)
    print("...")
    return {"pairings": pairs}


def get_restaurant(id):
    response = req.get(
        "https://roo-api-sandbox.deliveroo.net/restaurants/{}".format(id),
        params={},
        headers={"content-type": "application/json", "api-key": auth},
    )
    json_data = json.loads(response.text)
    return json_data


def is_restuarant_closed(id):
    restaurant = get_restaurant(id)
    return restaurant["status"] == "CLOSED"


def get_restaurant_lat_long(id):
    restaurant = get_restaurant(id)
    loc = restaurant["location"]
    return (float(loc["lat"]), float(loc["long"]))


def get_orders():
    response = req.get(
        "https://roo-api-sandbox.deliveroo.net/orders",
        params={},
        headers={"content-type": "application/json", "api-key": auth},
    )
    json_data = json.loads(response.text)
    return json_data


def get_riders():
    response = req.get(
        "https://roo-api-sandbox.deliveroo.net/riders",
        params={},
        headers={"content-type": "application/json", "api-key": auth},
    )
    json_data = json.loads(response.text)
    return json_data


def get_rider(id):
    response = req.get(
        "https://roo-api-sandbox.deliveroo.net/riders/{}".format(id),
        params={},
        headers={"content-type": "application/json", "api-key": auth},
    )
    json_data = json.loads(response.text)
    return json_data


def get_rider_lat_long(id):
    rider = get_rider(id)
    loc = rider["location"]
    return (float(loc["lat"]), float(loc["long"]))


def shortest_path(order, rider):
    return float(
        "{0:.5f}".format(
            ((order[0] - rider[0]) ** 2 + (order[1] - rider[1])) ** 0.5)
    )


# def calculateDistance(x1, y1, x2, y2):
#     dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
#     return dist

def distance(restaurantlatlong, riderlatlong):
    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(restaurantlatlong[0])
    lon1 = radians(restaurantlatlong[1])
    lat2 = radians(riderlatlong[0])
    lon2 = radians(riderlatlong[1])
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return float("{:0.2f}".format(distance))


def pairings(orders, riders):
    usable_riders = riders
    pairings = []
    for order in orders:
        smallest = {"d": 100}
        i = 0
        while i < len(usable_riders):
            rider = usable_riders[i]
            loc = rider["location"]
            riderlatlong = (float(loc["lat"]), float(loc["long"]))
            restaurantlatlong = get_restaurant_lat_long(order["restaurant_id"])

            d = distance(restaurantlatlong, riderlatlong)
            if d < smallest["d"]:
                smallest = rider
                usable_riders.remove(rider)
                smallest["d"] = d
                break
            i += 1
        pairings.append({"order": {"id": order["id"],
                                   "description": order["order_items"]},
                         "distance": d,
                         "restaurant": {
            "id": order["restaurant_id"],
            "location": {
                "lat": restaurantlatlong[0],
                "long": restaurantlatlong[1]
            }},
            "rider": {
                "id": rider["id"],
            "name": rider["name"],
            "location": {
                "lat": riderlatlong[0],
                "long": riderlatlong[1]
                }
        }
        })
    return pairings


if __name__ == "__main__":

    app.run()
