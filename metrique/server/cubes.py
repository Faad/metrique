#!/usr/bin/env python
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# Author: "Chris Ward <cward@redhat.com>

import logging
logger = logging.getLogger(__name__)

from metrique.server.config import mongodb
from metrique.server.defaults import MONGODB_CONF

mongodb_config = mongodb(MONGODB_CONF)
ETL_ACTIVITY = mongodb_config.c_etl_activity


def get_cube(cube, admin=True, timeline=False):
    ''' return back a mongodb connection to give cube collection '''
    if timeline:
        if admin:
            return mongodb_config.db_timeline_admin.db[cube]
        else:
            return mongodb_config.db_timeline_data.db[cube]
    else:
        if admin:
            return mongodb_config.db_warehouse_admin.db[cube]
        else:
            return mongodb_config.db_warehouse_data.db[cube]


def get_etl_activity():
    return ETL_ACTIVITY


def get_fields(cube, fields=None):
    ''' return back a list of fields found in documents of a given cube '''
    if not fields:
        return []
    cube_fields = list_cube_fields(cube)
    if not cube_fields:
        return []
    elif fields == '__all__':
        return cube_fields
    else:  # fields
        if isinstance(fields, basestring):
            fields = [s.strip() for s in fields.split(',')]
            return fields


def list_cube_fields(cube):
    return ETL_ACTIVITY.find_one({'_id': cube})


def list_cubes():
    '''
        Get a list of cubes server exports
        (optionally) filter out cubes user can't 'r' access
    '''
    names = mongodb_config.db_warehouse_data.db.collection_names()
    return [n for n in names if not n.startswith('system')]
