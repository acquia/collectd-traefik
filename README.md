# collectd-traefik

A [Traefik](https://traefik.io/) plugin for [collectd](https://collectd.org/)
using collectd's [Python plugin](https://collectd.org/documentation/manpages/collectd-python.5.shtml).

The plugin captures following metrics:

* `uptime_sec` - Total time of daemon uptime
* `total_count` - Total proxied requests
* `total_response_time_sec` - Total time spent in requests
* `average_response_time_sec` - Average response time
* `status_code_count/[CODE]` - Number of responses in flight
* `total_status_code_count/[CODE]` - Total number of responses with given code

## Install

1. Place `traefik.py` in `/opt/collectd/lib/collectd/plugins/python` (assuming
   you have collectd installed to `/opt/collectd`).

2. Configure the plugin (see below).

3. Restart collectd.

## Configuration

Its necessary to enable [API backend](https://docs.traefik.io/toml/#api-backend)
on a traefik instance that is accessible to collectd so it can access `/health`
url. In the example configuration the backend is enabled on a port `8080`.

Add the following to your collectd config or use the included `traefik.conf`.

```
<LoadPlugin python>
  Globals true
</LoadPlugin>

<Plugin python>
  ModulePath "/opt/collectd/lib/collectd/plugins/python"
  LogTraces true
  Interactive false
  Import "traefik"

  <Module traefik>
    Instance "prod"
    Host "localhost"
    Port 8080
    Verbose false
    Version "1.1.1"
  </Module>
</Plugin>
```

Plugin supports multiple instances to be configured.

This plugin was tested with Traefik version `1.1.1`.

## Credits

When writing this code I was using code from:

* https://github.com/rayrod2030/collectd-mesos
* https://github.com/powdahound/redis-collectd-plugin
