#!/usr/bin/env python

import time
import os

import pg8000
import requests

from flask import Flask, jsonify, request

VERSION = "0.0.1"

pg8000.paramstyle = 'named'

app = Flask(__name__)

USER_URL = "http://usersvc:5000/%s"
GRUE_LIST_URL = "http://gruesvc:5000/grue"
GRUE_URL = "http://gruesvc:5000/grue/%s"

MAZE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS maze (
    mazename VARCHAR(64) NOT NULL,
    cell VARCHAR(16) NOT NULL,
    state VARCHAR(16),
    metadata VARCHAR(16)
)
'''

class RichStatus (object):
    def __init__(self, ok, **kwargs):
        self.ok = ok
        self.info = kwargs

    # Remember that __getattr__ is called only as a last resort if the key
    # isn't a normal attr.
    def __getattr__(self, key):
        return self.info.get(key)

    def __nonzero__(self):
        return self.ok

    def __str__(self):
        attrs = ["%s=%s" % (key, self.info[key]) for key in sorted(self.info.keys())]
        astr = " ".join(attrs)

        if astr:
            astr = " " + astr

        return "<RichStatus %s%s>" % ("OK" if self else "BAD", astr)

    def toDict(self):
        d = { 'ok': self.ok }

        for key in self.info.keys():
            d[key] = self.info[key]

        return d

    @classmethod
    def fromError(self, error, **kwargs):
        kwargs['error'] = error
        return RichStatus(False, **kwargs)

    @classmethod
    def OK(self, **kwargs):
        return RichStatus(True, **kwargs)


def setup():
    # try:
    #     conn = get_db("postgres")
    #     conn.autocommit = True

    #     cursor = conn.cursor()
    #     cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'maze'")
    #     results = cursor.fetchall()
    #     if not results:
    #         cursor.execute("CREATE DATABASE maze")
    #     conn.commit()
    #     conn.close()
    # except pg8000.Error as e:
    #     return RichStatus.fromError("no maze database: %s" % e)

    # try:
    #     conn = get_db("maze")
    #     cursor = conn.cursor()
    #     cursor.execute(MAZE_TABLE_SQL)
    #     conn.commit()
    #     conn.close()
    # except pg8000.Error as e:
    #     return RichStatus.fromError("no maze table: %s" % e)

    return RichStatus.OK()

def map_result(r):
    rc = RichStatus.fromError("impossible error")

    if r.status_code == 200:
        return jsonify(r.json())
    else:
        rc = RichStatus.fromError("request failed: %s" % r.text)

        return jsonify(rc.toDict())

# @app.route('/user', methods=[ 'GET' ])
# def handle_user_list():
#     r = requests.get(USER_LIST_URL)

#     return map_result(r)

@app.route('/maze/user/<username>', methods=[ 'GET', 'PUT' ])
def handle_user(username):
    url = USER_URL % username

    if request.method == 'PUT':
        r = requests.put(url, json=request.get_json())
    elif request.method == 'GET':
        r = requests.get(url)

    return map_result(r)

@app.route('/maze/grue', methods=[ 'GET', 'POST' ])
def handle_grue_list():
    if request.method == 'POST':
        r = requests.post(GRUE_LIST_URL, json=request.get_json())
    elif request.method == 'GET':
        r = requests.get(GRUE_LIST_URL)

    return map_result(r)

@app.route('/maze/grue/<grueuuid>', methods=[ 'GET', 'PUT' ])
def handle_grue(grueuuid):
    url = GRUE_URL % grueuuid

    if request.method == 'PUT':
        r = requests.put(url, json=request.get_json())
    elif request.method == 'GET':
        r = requests.get(url)

    return map_result(r)

@app.route('/maze/health', methods=['GET', 'HEAD'])
def health():
    # TODO: Custom health check logic.
    return jsonify(RichStatus.OK(msg="mazesvc %s OK" % VERSION).toDict())


def main():
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    setup()
    main()
