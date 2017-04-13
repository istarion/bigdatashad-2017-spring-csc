#!/usr/bin/env python

import argparse
import datetime
import getpass
import hashlib
import random
import re
import struct

from flask import Flask, request, abort, jsonify
from functools import wraps

app = Flask(__name__)
app.secret_key = "my_secret_key"


def iterate_between_dates_by_hour(start_date, end_date):
    span = end_date - start_date
    for i in xrange((span.days + 1) * 24):
        yield start_date + datetime.timedelta(seconds=3600 * i)


def iterate_between_dates(start_date, end_date):
    span = end_date - start_date
    for i in xrange(span.days + 1):
        yield start_date + datetime.timedelta(days=i)


def inject_start_end_date(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start_date = request.args.get("start_date", None)
        end_date = request.args.get("end_date", None)

        if start_date is None or end_date is None:
            abort(400)

        try:
            start_date = datetime.datetime(*map(int, start_date.split("-")))
            end_date = datetime.datetime(*map(int, end_date.split("-")))
        except ValueError:
            abort(400)

        return fn(start_date=start_date, end_date=end_date, *args, **kwargs)
    return wrapper


def inject_user_ip(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_ip = request.args.get("user_ip", None)

        if user_ip is None or re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", user_ip) is None:
            abort(400)

        return fn(user_ip=user_ip, *args, **kwargs)
    return wrapper


def inject_profile_id(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        profile_id = request.args.get("profile_id", None)

        if profile_id is None or re.match(r"^id\d+$", profile_id) is None:
            abort(400)

        return fn(profile_id=profile_id, *args, **kwargs)
    return wrapper


@app.route("/")
def index():
    return "OK!"


@app.route("/api/hw2/user_hits")
@inject_start_end_date
@inject_user_ip
def api_hw2_user_hits(start_date, end_date, user_ip):
    result = {}
    for hour in iterate_between_dates_by_hour(start_date, end_date):
        user_hits = int(random.normalvariate(1000, 50))
        result[hour.strftime("%Y-%m-%dT%H:%M")] = user_hits
    return jsonify(result)


@app.route("/api/hw2/user_visited_profiles")
@inject_start_end_date
@inject_user_ip
def api_hw2_user_visited_profiles(start_date, end_date, user_ip):
    result = {}
    for date in iterate_between_dates(start_date, end_date):
        visited_profiles = [("id%d" % random.randint(10000, 99999)) for i in xrange(10)]
        result[date.strftime("%Y-%m-%d")] = visited_profiles
    return jsonify(result)


@app.route("/api/hw2/profile_hits")
@inject_start_end_date
@inject_profile_id
def api_hw2_profile_hits(start_date, end_date, profile_id):
    result = {}
    for hour in iterate_between_dates_by_hour(start_date, end_date):
        profile_hits = int(random.normalvariate(1000, 50))
        result[hour.strftime("%Y-%m-%dT%H:%M")] = profile_hits
    return jsonify(result)


@app.route("/api/hw2/profile_users")
@inject_start_end_date
@inject_profile_id
def api_hw2_profile_users(start_date, end_date, profile_id):
    result = {}
    for date in iterate_between_dates(start_date, end_date):
        profile_users = int(random.normalvariate(100, 5))
        result[date.strftime("%Y-%m-%d")] = profile_users
    return jsonify(result)


@app.route("/api/hw2/user_profile_hits")
@inject_start_end_date
@inject_user_ip
@inject_profile_id
def api_hw2_user_profile_hits(start_date, end_date, user_ip, profile_id):
    result = {}
    for date in iterate_between_dates(start_date, end_date):
        user_profile_hits = int(random.normalvariate(10, 3))
        result[date.strftime("%Y-%m-%d")] = user_profile_hits
    return jsonify(result)


def login_to_port(login):
    """
    We believe this method works as a perfect hash function
    for all course participants. :)
    """
    hasher = hashlib.new("sha1")
    hasher.update(login)
    values = struct.unpack("IIIII", hasher.digest())
    folder = lambda a, x: a ^ x + 0x9e3779b9 + (a << 6) + (a >> 2)
    return 10000 + reduce(folder, values) % 20000


def main():
    parser = argparse.ArgumentParser(description="HW 2 Example")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=login_to_port(getpass.getuser()))
    parser.add_argument("--debug", action="store_true", dest="debug")
    parser.add_argument("--no-debug", action="store_false", dest="debug")
    parser.set_defaults(debug=False)

    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
