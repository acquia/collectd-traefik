'''
Traefik collectd plugin written in Python.
'''

import collectd
import json
import urllib2
import socket
import collections


PLUGIN_NAME = 'traefik'
TRAEFIK_INSTANCE = ""
TRAEFIK_HOST = "localhost"
TRAEFIK_PORT = 8080
TRAEFIK_VERSION = "1.1.1"
TRAEFIK_URL = ""
VERBOSE_LOGGING = False


CONFIGS = []


collectd.info('traefik: Loading Python plugin:' + PLUGIN_NAME)


_Stat = collections.namedtuple('Stat', ('type', 'path'))
class Stat(_Stat):
    """Stat is a single statistic definition"""

    def value_from_json(self, data):
        """Try to read nested path in provided data object"""
        parts = self.path.split('/')
        value = data

        while len(parts) > 0:
            key = parts.pop(0)
            if key in value:
                value = value[key]
            else:
                return None

        return value


# Stats definition
STATS = {
    'uptime_sec' : Stat('counter', 'uptime_sec'),
    'total_count' : Stat('counter', 'total_count'),
    'total_response_time_sec' : Stat('counter', 'total_response_time_sec'),
    'average_response_time_sec' : Stat('gauge', 'average_response_time_sec'),
}


# List of valid HTTP codes
HTTP_CODES = [
    100, 101, 102,
    200, 201, 202, 203, 204, 205, 206, 207, 208, 226,
    300, 301, 302, 303, 304, 305, 306, 307, 308,
    400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414,
        415, 416, 417, 421, 422, 423, 424, 426, 428, 429, 431, 451,
    500, 501, 502, 503, 504, 505, 506, 507, 508, 510, 511,
]


for HTTP_CODE in HTTP_CODES:
    in_flight_path = 'status_code_count/{}'.format(HTTP_CODE)
    STATS[in_flight_path] = Stat('gauge', in_flight_path)
    # Total counts
    total_path = 'total_status_code_count/{}'.format(HTTP_CODE)
    STATS[total_path] = Stat('counter', total_path)


def configure_callback(conf):
    """Received configuration information"""
    host = TRAEFIK_HOST
    port = TRAEFIK_PORT
    verboseLogging = VERBOSE_LOGGING
    version = TRAEFIK_VERSION
    instance = TRAEFIK_INSTANCE
    for node in conf.children:
        if node.key == 'Host':
            host = node.values[0]
        elif node.key == 'Port':
            port = int(node.values[0])
        elif node.key == 'Verbose':
            verboseLogging = bool(node.values[0])
        elif node.key == 'Version':
            version = node.values[0]
        elif node.key == 'Instance':
            instance = node.values[0]
        else:
            collectd.warning('traefik plugin: Unknown config key: %s.' % node.key)
            continue

    log_verbose(verboseLogging, 'traefik plugin configured with host = %s, port = %s, verbose logging = %s, version = %s, instance = %s' % (
      host, port, verboseLogging, version, instance))

    CONFIGS.append({
        'host': host,
        'port': port,
        'url': 'http://' + host + ':' + str(port) + '/health',
        'verboseLogging': verboseLogging,
        'version': version,
        'instance': instance,
    })


def read():
    for conf in CONFIGS:
      try:
          result = json.load(urllib2.urlopen(conf['url'], timeout=10))
      except urllib2.URLError, e:
          collectd.error('traefik plugin: Error connecting to %s - %r' % (conf['mesos_url'], e))
          return None
      parse_stats(conf, result)


def parse_stats(conf, result):
    for stat in STATS.values():
        value = stat.value_from_json(result)
        if value:
          log_verbose(conf['verboseLogging'], 'Sending value[%s]: %s=%s for instance:%s' % (stat.type, stat.path, value, conf['instance']))

          val = collectd.Values(plugin=PLUGIN_NAME)
          val.type = stat.type
          val.type_instance = stat.path
          val.values = [value]
          val.plugin_instance = conf['instance']
          # https://github.com/collectd/collectd/issues/716
          val.meta = {'0': True}
          val.dispatch()


def log_verbose(enabled, msg):
    if not enabled:
        return
    collectd.info('traefik plugin [verbose]: %s' % msg)


# Register our callbacks to collectd
collectd.register_config(configure_callback)
collectd.register_read(read)
