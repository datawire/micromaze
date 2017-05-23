#!/usr/bin/env python

import time
import os

import pg8000
from flask import Flask, jsonify

VERSION = "0.0.1"

pg8000.paramstyle = 'named'

app = Flask(__name__)

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
    try:
        conn = get_db("postgres")
        conn.autocommit = True

        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'maze'")
        results = cursor.fetchall()
        if not results:
            cursor.execute("CREATE DATABASE maze")
        conn.commit()
        conn.close()
    except pg8000.Error as e:
        return RichStatus.fromError("no maze database: %s" % e)

    try:
        conn = get_db("maze")
        cursor = conn.cursor()
        cursor.execute(MAZE_TABLE_SQL)
        conn.commit()
        conn.close()
    except pg8000.Error as e:
        return RichStatus.fromError("no maze table: %s" % e)

    return RichStatus.OK()

def cell_key(row, column):
    return "r%02dc%02d" % (row, column)

def initialize_maze(name, width, height):
    conn = get_db("maze")
    cursor = conn.cursor()
    # cursor.execute("BEGIN TRANSACTION");

    try:
        cursor.execute("DELETE FROM maze WHERE mazename = ':name'", locals())
    except pg8000.Error as e:
        return RichStatus.fromError("could not delete old %s: %s" % (name, e))

    try:
        for col in range(width):
            for row in range(height):
                key = cell_key(row, col)
                state = '____'
                metadata = ''

                # sql = 'INSERT INTO maze VALUES ("%(name)s", "%(cellkey)s", "%(state)s", "%(metadata)s")' % locals()
                # print(sql)
                cursor.execute("INSERT INTO maze VALUES (:name, :key, :state, :metadata)", locals())

        conn.commit()
    except pg8000.Error as e:
        return RichStatus.fromError("could not initialize %s: %s" % (name, e))

    return RichStatus.OK()

def list_mazes():
    try:
        conn = get_db("maze")
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT(mazename) FROM maze ORDER BY mazename", locals())

        mazenames = [ r[0] for r in cursor ]

        return RichStatus.OK(mazes=mazenames)
    except pg8000.Error as e:
        return RichStatus.fromError("could not list mazes:: %s" % e)

def get_cell(maze, row, column, direction):
    try:
        conn = get_db("maze")
        cursor = conn.cursor()

        key = cell_key(row, column)

        cursor.execute("SELECT state, metadata FROM maze WHERE mazename = :maze AND cell = :key", locals())
        [ state, metadata ] = cursor.fetchone()

        if direction is not None:
            state = state[int(direction)]

        return RichStatus.OK(state=state, metadata=metadata)
    except pg8000.Error as e:
        return RichStatus.fromError("could not get cell %s %s: %s" % (maze, key, e))

def get_db(database):
    db_host = "postgres"
    db_port = 5432

    if "MAZE_DB_RESOURCE_HOST" in os.environ:
        db_host = os.environ["MAZE_DB_RESOURCE_HOST"]

    if "MAZE_DB_RESOURCE_PORT" in os.environ:
        db_port = int(os.environ["MAZE_DB_RESOURCE_PORT"])

    return pg8000.connect(user="postgres", password="postgres",
                          database=database, host=db_host, port=db_port)

@app.route('/maze/<name>/<width>/<height>', methods=['PUT'])
def newMaze(name, width, height):
    rc = RichStatus.fromError("impossible error")

    try:
        rc = setup()

        if rc:
            rc = initialize_maze(name, int(width), int(height))
    except Exception as e:
        rc = RichStatus.fromError("%s: initialization failed: %s" % (name, e))

    return jsonify(rc.toDict())

@app.route('/maze/<name>', methods=['GET'])
def fetch_cell(name):
    rc = RichStatus.fromError("impossible error")

    try:
        args = request.args.to_dict()

        row = args.get('row', None)
        col = args.get('col', None)
        direction = args.get('dir', None)

        if not row or not col:
            rc = RichStatus.fromError("row and col are required")
        else:
            rc = setup()

            if rc:
                rc = get_cell(name, int(row), int(col), direction)
    except Exception as e:
        rc = RichStatus.fromError("%s: get %s, %s failed: %s" % (name, row, column, e))

    return jsonify(rc.toDict())

@app.route('/maze/<name>/<row>/<col>/<direction>', methods=['GET'])
def fetch_cell2(name):
    rc = RichStatus.fromError("impossible error")

    try:
        rc = setup()

        if rc:
            rc = get_cell(name, int(row), int(col), direction)
    except Exception as e:
        rc = RichStatus.fromError("%s: get %s, %s failed: %s" % (name, row, column, e))

    return jsonify(rc.toDict())

@app.route('/maze/<name>/<row>/<column>', methods=['PUT'])
def update_cell(name, row, column):
    rc = RichStatus.fromError("impossible error")
    
    try:
        rc = setup()

        if rc:
            rc = get_cell(name, int(row), int(column))
    except Exception as e:
        rc = RichStatus.fromError("%s: get %s, %s failed: %s" % (name, row, column, e))

    return jsonify(rc.toDict())


@app.route('/maze', methods=['GET'])
def list_all():
    rc = list_mazes()

    return jsonify(rc.toDict())


@app.route('/maze/health', methods=['GET', 'HEAD'])
def health():
    # TODO: Custom health check logic.
    return jsonify(RichStatus.OK(msg="mazesvc %s OK" % VERSION).toDict())


def main():
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    setup()
    main()
