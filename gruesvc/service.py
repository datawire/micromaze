#!/usr/bin/env python

import logging
import os
import socket
import time
import uuid

import pg8000
from flask import Flask, jsonify, request

Version = "0.1.0"

pg8000.paramstyle = 'named'

MyHostName = socket.gethostname()
MyResolvedName = socket.gethostbyname(socket.gethostname())

logging.basicConfig(
    level=logging.DEBUG, # if appDebug else logging.INFO,
    format="%%(asctime)s gruesvc %s %%(levelname)s: %%(message)s" % Version,
    datefmt="%Y-%m-%d %H:%M:%S"
)

logging.info("initializing on %s (resolved %s)" % (MyHostName, MyResolvedName))

app = Flask(__name__)

GRUE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS grues (
    uuid VARCHAR(64) NOT NULL PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    location VARCHAR(2048) NOT NULL,
    hunger INTEGER NOT NULL,
    meals INTEGER NOT NULL
)
'''

class RichStatus (object):
    def __init__(self, ok, **kwargs):
        self.ok = ok
        self.info = kwargs
        self.info['hostname'] = MyHostName
        self.info['resolvedname'] = MyResolvedName

    # Remember that __getattr__ is called only as a last resort if the key
    # isn't a normal attr.
    def __getattr__(self, key):
        return self.info.get(key)

    def __nonzero__(self):
        return self.ok

    def __str__(self):
        attrs = ["%=%s" % (key, self.info[key]) for key in sorted(self.info.keys())]
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

def get_db(database):
    db_host = "postgres"
    db_port = 5432

    if "GRUE_DB_RESOURCE_HOST" in os.environ:
        db_host = os.environ["GRUE_DB_RESOURCE_HOST"]

    if "GRUE_DB_RESOURCE_PORT" in os.environ:
        db_port = int(os.environ["GRUE_DB_RESOURCE_PORT"])

    return pg8000.connect(user="postgres", password="postgres",
                          database=database, host=db_host, port=db_port)

def setup():
    try:
        conn = get_db("postgres")
        conn.autocommit = True

        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'grues'")
        results = cursor.fetchall()

        if not results:
            cursor.execute("CREATE DATABASE grues")

        conn.close()
    except pg8000.Error as e:
        return RichStatus.fromError("no grue database in setup: %s" % e)

    try:
        conn = get_db("grues")
        cursor = conn.cursor()
        cursor.execute(GRUE_TABLE_SQL)
        conn.commit()
        conn.close()
    except pg8000.Error as e:
        return RichStatus.fromError("no grue table in setup: %s" % e)

    return RichStatus.OK()

def getIncomingJSON(req, *needed):
    try:
        incoming = req.get_json()
    except Exception as e:
        return RichStatus.fromError("invalid JSON: %s" % e)

    logging.debug("getIncomingJSON: %s" % incoming)

    if not incoming:
        incoming = {}

    missing = []

    for key in needed:
        if key not in incoming:
            missing.append(key)

    if missing:
        return RichStatus.fromError("Required fields missing: %s" % " ".join(missing))
    else:
        return RichStatus.OK(**incoming)

########
# USER CRUD

def handle_grue_list(req):
    try:
        conn = get_db("grues")
        cursor = conn.cursor()

        cursor.execute("SELECT uuid, name, location, hunger, meals FROM grues ORDER BY meals, hunger", locals())

        grues = []

        for grueuuid, name, location, hunger, meals in cursor:
            grues.append({ 'uuid': grueuuid, 'name': name, 'location': location, 'hunger': hunger, 'meals': meals })

        return RichStatus.OK(grues=grues, count=len(grues))
    except pg8000.Error as e:
        return RichStatus.fromError("grues: could not fetch info: %s" % e)

def handle_grue_get(req, grueuuid):
    try:
        conn = get_db("grues")
        cursor = conn.cursor()

        cursor.execute("SELECT uuid, name, location, hunger, meals FROM grues WHERE uuid = :grueuuid", locals())
        [ grueuuid, name, location, hunger, meals ] = cursor.fetchone()

        return RichStatus.OK(uuid=grueuuid, name=name, location=location, hunger=hunger, meals=meals)
    except pg8000.Error as e:
        return RichStatus.fromError("%s: could not fetch info: %s" % (grueuuid, e))

def handle_grue_del(req, grueuuid):
    try:
        conn = get_db("grues")
        cursor = conn.cursor()

        cursor.execute("DELETE FROM grues WHERE uuid = :grueuuid", locals())
        conn.commit()

        return RichStatus.OK(uuid=grueuuid)
    except pg8000.Error as e:
        return RichStatus.fromError("%s: could not delete grue: %s" % (grueuuid, e))

def handle_grue_post(req):
    try:
        rc = getIncomingJSON(req, 'name', 'location')

        logging.debug("handle_grue_post: got args %s" % rc.toDict())

        if not rc:
            return rc

        name = rc.name
        location = rc.location
        hunger = 0
        meals = 0

        grueuuid = uuid.uuid4().hex.upper();

        logging.debug("handle_grue_post: grueuuid %s is %s @ %s" % (grueuuid, name, location))

        conn = get_db("grues")
        cursor = conn.cursor()

        cursor.execute('INSERT INTO grues VALUES(:grueuuid, :name, :location, :hunger, :meals)', locals())
        conn.commit()

        return RichStatus.OK(uuid=grueuuid)
    except pg8000.Error as e:
        return RichStatus.fromError("%s: could not save info: %s" % (grueuuid, e))

def handle_grue_put(req, grueuuid):
    incoming = {}

    try:
        incoming = req.get_json()
    except Exception as e:
        return RichStatus.fromError("invalid JSON: %s" % e)

    logging.debug("handle_grue_put %s: %s" % (grueuuid, incoming))

    if not incoming:
        incoming = {}

    updates = {}

    for key, transform in [ ('location', str ), ('hunger', int), ('meals', int) ]:
        if key in incoming:
            try:
                updates[key] = transform(incoming[key])
            except Exception as e:
                return RichStatus.fromError("%s: bad value for %s: %s" % (grueuuid, key, incoming[key]))

    if not updates:
        return RichStatus.fromError("%s: need location, hunger, and/or meals")

    setClauses = ", ".join([ "%s = :%s" % (x, x) for x in sorted(updates.keys())])

    sql = 'UPDATE grues SET %s WHERE uuid = :grueuuid' % setClauses

    # Add 'grueuuid' to updates so we can bind our SQL against that.
    updates['grueuuid'] = grueuuid

    try:
        logging.debug("handle_grue_put %s: updates %s" % (grueuuid, updates))
        logging.debug("handle_grue_put %s: SQL %s" % (grueuuid, sql))

        conn = get_db("grues")
        cursor = conn.cursor()

        cursor.execute(sql, updates)
        conn.commit()

        return handle_grue_get(req, grueuuid)
    except pg8000.Error as e:
        return RichStatus.fromError("%s: could not update info: %s" % (grueuuid, e))    

@app.route('/grue', methods=[ 'POST', 'GET' ])
def handle_grue_root():
    rc = RichStatus.fromError("impossible error")
    logging.debug("handle_grue_root: method %s" % request.method)
    
    try:
        rc = setup()

        if rc:
            if request.method == 'POST':
                rc = handle_grue_post(request)
            else:
                rc = handle_grue_list(request)
    except Exception as e:
        logging.exception(e)
        rc = RichStatus.fromError("root: %s failed: %s" % (request.method, e))

    return jsonify(rc.toDict())

@app.route('/grue/<grueuuid>', methods=[ 'PUT', 'GET', 'DELETE' ])
def handle_grue(grueuuid):
    rc = RichStatus.fromError("impossible error")
    logging.debug("handle_grue %s: method %s" % (grueuuid, request.method))
    
    try:
        rc = setup()

        if rc:
            if request.method == 'PUT':
                rc = handle_grue_put(request, grueuuid)
            elif request.method == 'DELETE':
                rc = handle_grue_del(request, grueuuid)
            else:
                rc = handle_grue_get(request, grueuuid)
    except Exception as e:
        logging.exception(e)
        rc = RichStatus.fromError("%s: %s failed: %s" % (grueuuid, request.method, e))

    return jsonify(rc.toDict())

@app.route('/grue/health')
def root():
    rc = RichStatus.OK(msg="grue health check OK")

    return jsonify(rc.toDict())

def main():
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    setup()
    main()
