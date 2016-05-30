#!/usr/bin/env python2
import os
from datetime import datetime, timedelta
from functools import partial
import logging
import time

from concurrent.futures import ThreadPoolExecutor

import pyrax

log = logging.getLogger("pyrax-ping-watcher")

REBOOT_THRESHOLD = 10 # ping availability threshold (percent)
AVAILABILITY_WINDOW = 300 # ping availability sample window (seconds)

def find_ping(server):
    """Get ping check for a given server"""
    cm = pyrax.cloud_monitoring
    entities = [ e for e in cm.list_entities() if e.label == server.name ]
    if not entities:
        log.warning("No entity for %s", server.name)
        return
    entity = entities[0]
    
    pings = [ check for check in cm.list_checks(entity) if check.type == 'remote.ping' ]
    if not pings:
        log.debug("No pings for %s", server.name)
        return
        # ping = create_ping_check(server, entity)
    else:
        ping = pings[0]
    return ping

def get_availability(server):
    """Get availability percentage of a given server"""
    ping = find_ping(server)
    if not ping:
        return
    metrics = [ m for m in ping.list_metrics() if m.name.endswith('.available') ]
    # timezone?
    end = datetime.now()
    start = end - timedelta(seconds=AVAILABILITY_WINDOW)
    
    points = []
    for m in metrics:
        data = ping.get_metric_data_points(m.name, start, end, resolution='FULL')
        points.extend([p['average'] for p in data])
    if not points:
        log.warning("No points for %s" % server.name)
        return
    # return mean of our sample
    try:
        return 1.0 * sum(points) / len(points)
    except Exception:
        log.exception("Failed to compute availability of %s", server.name)
        log.error("data=%s", data)

def check_ping(server):
    """Checks ping-availability of a server
    
    If availability is below a threshold, reboot the server
    """
    log.info("Checking ping for server %s", server.name)
    avail = get_availability(server)
    if avail is None:
        return
    if avail < REBOOT_THRESHOLD:
        log.warning("Rebooting %s: %.0f < %.0f%%", server.name, avail, REBOOT_THRESHOLD)
        # since this is experimental, only apply it to tmpnb.org:
        if 'tmpnb.org' in server.name:
            server.reboot()
    else:
        log.info("Server %s is up (%.0f%%)", server.name, avail)

def check_region_pings(pool, region):
    """Check pings for all servers in a given region"""
    cs = pyrax.connect_to_cloudservers(region=region)
    log.info("Checking pings for %s", region)
    servers = cs.servers.findall()
    log.debug("%3i servers in Region %s", len(servers), region)
    list(pool.map(check_ping, servers))


def main(interval=300, threads=10):
    pool = ThreadPoolExecutor(threads)
    while True:
        regions = pyrax.identity.services['compute'].endpoints.keys()
        tosleep = interval / len(regions)
        for region in regions:
            check_region_pings(pool, region)
            log.info("Sleeping for %i seconds", tosleep)
            time.sleep(tosleep)


if __name__ == '__main__':
    import argparse

    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(levelname).1s %(name)s] %(message)s')
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    log.addHandler(handler)
    pyrax.set_setting("identity_type", "rackspace")
    pyrax.set_credentials(os.environ["OS_USERNAME"], os.environ["OS_PASSWORD"])

    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', default=600, type=int,
        help="Interval (in seconds) to check servers"
    )
    parser.add_argument('--threads', default=10, type=int,
        help="Number of concurrent threads"
    )
    args = parser.parse_args()
    main(
        interval=args.interval,
        threads=args.threads,
    )