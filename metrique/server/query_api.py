#!/usr/bin/env python
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# Author: "Chris Ward <cward@redhat.com>

import logging
logger = logging.getLogger(__name__)
import pql
import re

from metrique.server.cubes import get_fields, get_cube
from metrique.server.job import job_save


@job_save('query distinct')
def distinct(cube, field):
    logger.debug('Running Distinct (%s.%s)' % (cube, field))
    _cube = get_cube(cube)
    return _cube.distinct(field)


@job_save('query count')
def count(cube, query):
    logger.debug('Running Count')
    pql_parser = pql.SchemaFreeParser()
    try:
        spec = pql_parser.parse(query)
    except Exception as e:
        raise ValueError("Invalid Query (%s)" % str(e))

    _cube = get_cube(cube)

    logger.debug('Mongo Query: %s' % spec)

    docs = _cube.find(spec)
    if docs:
        result = docs.count()
    else:
        result = 0
    docs.close()
    return result


def _get_date_pql_string(date, prefix=' and '):
    if date == '~':
        return ''

    dt_str = date.replace('T', ' ')
    dt_str = re.sub('(\+\d\d:\d\d)?$', '', dt_str)

    before = lambda d: '_start <= date("%s")' % d
    after = lambda d: '(_end >= date("%s") or _end == None)' % d
    split = date.split('~')
    logger.warn(split)
    if len(split) == 1:
        ret = '%s and %s' % (before(dt_str), after(dt_str))
    elif split[0] == '':
        ret = '%s' % before(split[1])
    elif split[1] == '':
        ret = '%s' % after(split[0])
    else:
        ret = '%s and %s' % (before(split[1]), after(split[0]))
    return prefix + ret


@job_save('query find')
def find(cube, query, fields=None, date=None,
         most_recent=True, sort=None, one=False):
    logger.debug('Running Find (%s)' % cube)
    if not sort:
        sort = [('_id', 1)]

    try:
        assert len(sort[0]) == 2
    except (AssertionError, IndexError, TypeError):
        raise ValueError("Invalid sort value; try [('_id': -1)]")

    logger.debug('... fields: %s' % fields)
    fields = sorted(get_fields(cube, fields))
    logger.debug('... matched fields (%s)' % fields)

    if date is not None:
        query += _get_date_pql_string(date)
        fields += ['_start', '_end', '_oid']

    logger.debug("PQL Query: %s" % query)
    pql_parser = pql.SchemaFreeParser()
    try:
        spec = pql_parser.parse(query)
    except Exception as e:
        raise ValueError("Invalid Query (%s): %s" % (str(e), query))

    _cube = get_cube(cube, timeline=(date is not None))

    logger.debug('Query: %s' % spec)

    if one:
        result = _cube.find_one(spec, fields, sort=sort)
    else:
        docs = _cube.find(spec, fields, sort=sort)
        docs.batch_size(10000000)  # hard limit is 16M...
        result = tuple(docs)
        docs.close()
    return result


def parse_ids(ids, delimeter=','):
    if isinstance(ids, basestring):
        ids = [s.strip() for s in ids.split(delimeter)]
    if type(ids) is not list:
        raise TypeError("ids expected to be a list")
    return ids


@job_save('query fetch')
def fetch(cube, fields=None, date=None, sort=None, skip=0, limit=0, ids=None):
    logger.debug('Running Fetch (skip:%s, limit:%s, ids:%s)' % (
        skip, limit, len(ids)))
    logger.debug('... Fields: %s' % fields)

    _cube = get_cube(cube, timeline=(date is not None))

    fields = get_fields(cube, fields)
    logger.debug('Return Fields: %s' % fields)

    if not sort:
        sort = [('_id', 1)]

    try:
        assert len(sort[0]) == 2
    except (AssertionError, IndexError, TypeError):
        raise ValueError("Invalid sort value; try [('_id': -1)]")

    if ids:
        spec = {'_id': {'$in': parse_ids(ids)}}
    else:
        spec = {}

    if date:
        fields += ['_start', '_end', '_oid']
        spec.update(pql.find(_get_date_pql_string(date, '')))

    docs = _cube.find(spec, fields, sort=sort,
                      skip=skip, limit=limit)
    docs.batch_size(10000000)  # hard limit is 16M...
    result = tuple(docs)
    docs.close()
    return result


@job_save('query aggregate')
def aggregate(cube, pipeline):
    logger.debug('Running Aggregation')
    logger.debug('Pipeline (%s): %s' % (type(pipeline), pipeline))
    _cube = get_cube(cube)
    return _cube.aggregate(pipeline)
