import os
import sys
import bottle
import datetime
import html

TOP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
[sys.path.append(dir_path) for dir_path in [TOP_DIR] if dir_path not in sys.path]

from big_brother.details.globals import PROJECT_DIR, DEFAULT_MONITORING_JSON_PATH, \
    MainProp, MetaProp, InstanceProp, DATETIME_FORMAT, USAGE_MEMO_PATH
from big_brother.details.utils import load_json, get_kib_size_as_human_readable_str


# Globals
# -- Application global variables (necessary evil)
APP = bottle.Bottle()
DATA_JSON_PATH = None
DEBUG = False
# --
REFRESH_TIME = 60  # 60s
# -- Default IO
DEFAULT_HOST = "192.168.10.132"  # drogon
DEFAULT_PORT = 1984
# -- Load average thresholds
LOW_LOAD_PERCENT = 5
MEDIUM_LOAD_PERCENT = 75
HIGH_LOAD_PERCENT = 200
# -- Memory usage thresholds
LOW_MEM_PERCENT = 5
MEDIUM_MEM_PERCENT = 75
HIGH_MEM_PERCENT = 90
# -- Disk space usage thresholds
LOW_SPACE_PERCENT = 5
MEDIUM_SPACE_PERCENT = 75
HIGH_SPACE_PRECENT = 90
# -- Uptime
LOW_UPTIME = 1
MEDIUM_UPTIME = 30
HIGH_UPTIME = 90
# -- Network rate thresholds (bits/s)
LOW_NET_RATE = 10 * 1024  # 10K
MEDIUM_NET_RATE = 1 * 1024 * 1024  # 1M
HIGH_NET_RATE = 100 * 1024 * 1024  # 100M


def run_server(host, port, data_json_path, debug):
    # Update app globals
    global DATA_JSON_PATH, DEBUG
    DATA_JSON_PATH = os.path.abspath(data_json_path)
    DEBUG = debug
    # Run server
    if DEBUG:
        # Development/debug mode, restart at each code change
        print("Debug mode enabled")
        bottle.run(APP, host=host, port=port, debug=True, reloader=True)
    else:
        # Production mode
        bottle.run(APP, host=host, port=port, server='paste')


# -----------------------------------------------------------------------------
# Routes

@APP.get('/')
def get_main_page():
    # Name
    page_title = "BigBrother"
    if DEBUG:
        page_title += " DEBUG"
    # Load monitoring results
    data = load_json(DATA_JSON_PATH)
    return create_html_page(data, page_title)


@APP.get('/favicon.ico')
def get_favicon():
    return bottle.static_file("favicon.ico", root=os.path.join(PROJECT_DIR, "images"))


# -----------------------------------------------------------------------------
# HTLM creation

def create_html_page(data, page_title):
    # Generate html content
    return f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{page_title}</title>
        <link rel="icon" type="image/x-icon" href="favicon.ico">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-gH2yIJqKdNHPEq0n4Mqa/HGKIhSkIHeL5AyhkYV8i59U5AR6csBvApHHNl/vI1Bx" crossorigin="anonymous">
        <meta http-equiv="refresh" content="{REFRESH_TIME}">
      </head>
      <body>
        <div class="container">
            <p></p>
            {create_html_head_banner(data)}
            {create_html_instances_table(data)}
            {create_html_storages_table(data)}
            {create_html_foot_banner(data)}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/js/bootstrap.bundle.min.js" integrity="sha384-A3rJD856KowSb7dwlZdYEkO39Gagi7vIsF0jrRAoQmDKKtQBHUuLZ9AsSv4jD4Xa" crossorigin="anonymous"></script>
        <p></p>
      </body>
    </html>
    """


def create_html_head_banner(data):
    last_update_timestamp = data[MainProp.METADATA][MetaProp.PROCESS_TIMESTAMP]
    last_update_datetime = datetime.datetime.strptime(last_update_timestamp, DATETIME_FORMAT)
    delta = datetime.datetime.now() - last_update_datetime
    delta_min = round(delta.total_seconds() / 60)
    return f"""
<div class="alert alert-primary bb-head-banner" role="alert">
    <strong>Last update</strong>: {last_update_timestamp} <i>({delta_min}min ago)</i>
</div>
"""


def create_html_instances_table(data):
    # Table header, on two lines
    thead = "<thead>"
    # -- Top line
    thead += f"""<tr>
    <th colspan="3" class="text-center">Instance</th>
    <th colspan="3" class="text-center">Load Average</th>
    <th colspan="3" class="text-center">Memory</th>
    <th colspan="3" class="text-center">Home Disk Space</th>
    <th colspan="2" class="text-center">Net. Rate (b/s)</th>
    <th colspan="1" class="text-center">Uptime</th>
    <th colspan="1" class="text-center">Usage Memo</th>
    </tr>"""
    # -- Second line
    thead += '<tr class="text-center">'
    # ---- Instance
    thead += f'<th>Name</th>'
    thead += f'<th>IP</th>'
    thead += f'<th>CPU(s)</th>'
    # ---- Load Average
    thead += f'<th>1min</th>'
    thead += f'<th>5min</th>'
    thead += f'<th>15min</th>'
    # ---- Memory
    thead += f'<th>Total</th>'
    thead += f'<th>Used</th>'
    thead += f'<th style="width: 10%">Usage</th>'
    # ---- Home Disk Space
    thead += f'<th>Total</th>'
    thead += f'<th>Used</th>'
    thead += f'<th style="width: 10%">Usage</th>'
    # ---- Network
    thead += f'<th>Sent</th>'
    thead += f'<th>Received</th>'
    # ---- Uptime
    thead += f'<th>Days</th>'
    # ---- Usage Memo
    thead += f'<th><small><samp>{USAGE_MEMO_PATH}</samp></small></th>'
    # --
    thead += "</tr>"
    thead += "</thead>"

    # Body
    tbody = "<tbody>"
    for instance_data in data[MainProp.INSTANCES]:
        trow = "<tr>"
        # Name
        trow += f"<td><strong>{instance_data[InstanceProp.NAME]}</strong></td>"
        # IP
        trow += f"<td><samp>{instance_data[InstanceProp.IP]}</samp></td>"
        # CPU
        trow += f"<td>{instance_data[InstanceProp.CPU_COUNT]}</td>"
        # Load averages
        for load_average in [instance_data[InstanceProp.LOAD_AVERAGE_1],
                             instance_data[InstanceProp.LOAD_AVERAGE_5],
                             instance_data[InstanceProp.LOAD_AVERAGE_15]]:
            load_ratio_percent = get_as_percentage(load_average, instance_data[InstanceProp.CPU_COUNT])
            trow += f"<td class='text-{get_load_average_color(load_ratio_percent)}'>" \
                    f"<strong>{get_load_average_as_str(load_average)}</strong></td>"
        # Memory
        mem_used = instance_data[InstanceProp.MEMORY_USED]
        mem_total = instance_data[InstanceProp.MEMORY_TOTAL]
        mem_used_percent = get_as_percentage(mem_used, mem_total)
        mem_usage_color = get_memory_usage_color(mem_used_percent)
        # -- Total
        trow += f"<td>{get_kib_size_as_human_readable_str(mem_total)}</td>"
        # -- Used
        trow += f"<td class='text-{mem_usage_color}'>" \
                f"<strong>{get_kib_size_as_human_readable_str(mem_used)}</strong></td>"
        # -- Usage
        trow += f"<td>{create_progressbar(mem_used_percent, mem_usage_color)}</td>"
        # Home disk space
        # Note: TOTAL != USED+AVAIL (ex: 5% reserved/root) --> "Usable" = TOTAL-AVAIL
        space_total = instance_data[InstanceProp.DISK_SPACE_TOTAL]
        space_used = substract(space_total, instance_data[InstanceProp.DISK_SPACE_AVAILABLE])
        space_used_percent = get_as_percentage(space_used, space_total)
        space_usage_color = get_disk_space_usage_color(space_used_percent)
        # -- total
        trow += f"<td>{get_kib_size_as_human_readable_str(space_total)}</td>"
        # -- Used
        trow += f"<td class='text-{space_usage_color}'>" \
                f"<strong>{get_kib_size_as_human_readable_str(space_used)}</strong></td>"
        # -- Usage
        trow += f"<td>{create_progressbar(space_used_percent, space_usage_color)}</td>"
        # Network
        send_rate = instance_data[InstanceProp.NET_SEND_RATE]
        received_rate = instance_data[InstanceProp.NET_RECEIVE_RATE]
        trow += f"<td class='text-{get_network_rate_color(send_rate)}'>" \
                f"<strong>{get_kib_size_as_human_readable_str(get_network_rate_in_kbits(send_rate))}</strong></td>"
        trow += f"<td class='text-{get_network_rate_color(received_rate)}'>" \
                f"<strong>{get_kib_size_as_human_readable_str(get_network_rate_in_kbits(received_rate))}</strong></td>"
        # Uptime
        uptime = instance_data[InstanceProp.UPTIME]
        trow += f"<td class='text-{get_uptime_color(uptime)}'>" \
                f"<strong>{uptime}</strong></td>"
        # Usage memo
        usage_memo = instance_data[InstanceProp.USAGE_MEMO]
        trow += f"<td class='text-{get_usage_memo_color(usage_memo)}'>" \
                f"<strong>{get_readable_usage_memo(usage_memo)}</strong></td>"
        # --
        trow += "</tr>"
        tbody += trow
    tbody += "</tbody>"
    # -- Wrap it all
    return f"""
<table class="table table-sm table-striped table-bordered text-end bb-instances-table">
    {thead}
    {tbody}
</table>
"""


def create_html_storages_table(data):
    # Table header, on two lines
    thead = "<thead>"
    # -- Top line
    thead += f"""<tr>
    <th colspan="3" class="text-center">Storage</th>
    <th colspan="3" class="text-center">Space</th>
    </tr>"""
    # -- Second line
    thead += '<tr class="text-center">'
    # ---- Storage
    thead += f'<th>Name</th>'
    thead += f'<th>Type</th>'
    thead += f'<th>Location</th>'
    # ---- Space
    thead += f'<th>Total</th>'
    thead += f'<th>Used</th>'
    thead += f'<th style="width: 40%">Usage</th>'
    # --
    thead += "</tr>"
    thead += "</thead>"

    # Table body
    tbody = "<tbody>"
    for storage_data in data[MainProp.STORAGES]:
        trow = "<tr>"
        # Name
        trow += f"<td><strong>{storage_data[InstanceProp.NAME]}</strong></td>"
        # Type
        storage_type = storage_data[InstanceProp.TYPE]
        storage_type_color = get_storage_type_color(storage_type)
        trow += f'<td class="table-{storage_type_color}">{storage_type}</td>'
        # Location
        host_ip = storage_data[InstanceProp.IP]
        disk_path = storage_data[InstanceProp.DISK_PATH]
        disk_file_system = storage_data[InstanceProp.DISK_FILE_SYSTEM]
        displayed_location = reformat_storage_location(storage_type, host_ip, disk_path, disk_file_system)
        trow += f"<td><samp>{displayed_location}</samp></td>"
        # Space
        # Note: TOTAL != USED+AVAIL (ex: 5% reserved/root) --> "Usable" = TOTAL-AVAIL
        space_total = storage_data[InstanceProp.DISK_SPACE_TOTAL]
        space_used = substract(space_total, storage_data[InstanceProp.DISK_SPACE_AVAILABLE])
        space_used_percent = get_as_percentage(space_used, space_total)
        space_usage_color = get_disk_space_usage_color(space_used_percent)
        # -- Total
        trow += f"<td>{get_kib_size_as_human_readable_str(space_total)}</td>"
        # -- Used
        trow += f"<td class='text-{space_usage_color}'>" \
                f"<strong>{get_kib_size_as_human_readable_str(space_used)}</strong></td>"
        # -- Usage
        trow += f"<td>{create_progressbar(space_used_percent, space_usage_color)}</td>"
        # --
        trow += "</tr>"
        tbody += trow
    tbody += "</tbody>"
    # -- Wrap it all
    return f"""
<table class="table table-sm table-striped table-bordered text-end bb-storages-table">
    {thead}
    {tbody}
</table>
"""


def get_load_average_as_str(value):
    # By default, commands such as df display the amount of memory in kibibytes
    if value is None:
        return str(value)
    return f"{value:.2f}"


def get_load_average_color(load_ratio_percent):
    if load_ratio_percent is None:
        return "secondary"  # Gray (unknown)
    elif load_ratio_percent < LOW_LOAD_PERCENT:
        return "primary"  # Blue (low / idle)
    elif load_ratio_percent < MEDIUM_LOAD_PERCENT:
        return "success"  # Green (medium)
    elif load_ratio_percent < HIGH_LOAD_PERCENT:
        return "warning"  # Yellow (high)
    else:
        return "danger"  # Red (very high / critical)


def get_as_percentage(num, denum):
    if num is None or denum is None:
        return None
    return 100 * num / denum


def substract(a, b):
    if a is None or b is None:
        return None
    return a - b


def get_memory_usage_color(mem_used_percent):
    if mem_used_percent is None:
        return "secondary"  # Gray (unknown)
    elif mem_used_percent < LOW_MEM_PERCENT:
        return "primary"  # Blue (low / idle)
    elif mem_used_percent < MEDIUM_MEM_PERCENT:
        return "success"  # Green (medium)
    elif mem_used_percent < HIGH_MEM_PERCENT:
        return "warning"  # Yellow (high)
    else:
        return "danger"  # Red (very high / critical)


def get_disk_space_usage_color(usage_percent):
    if usage_percent is None:
        return "secondary"  # Gray (unknown)
    elif usage_percent < LOW_SPACE_PERCENT:
        return "primary"  # Blue (low / idle)
    elif usage_percent < MEDIUM_SPACE_PERCENT:
        return "success"  # Green (medium)
    elif usage_percent < HIGH_SPACE_PRECENT:
        return "warning"  # Yellow (high)
    else:
        return "danger"  # Red (very high / critical)


def get_storage_type_color(storage_type):
    if storage_type == "Synology NAS":
        return "info"
    elif storage_type == "Ubuntu Share":
        return "warning"
    elif storage_type == "NetApp NAS":
        return "success"
    else:
        return "secondary"


def reformat_storage_location(storage_type, host_ip, disk_path, disk_file_system):
    if disk_file_system is None:
        return None
    # In most cases (NFS mount), disk_file_system will look like STORAGE_IP:/volume_path
    location = disk_file_system  # NAS_IP:/volume_name
    if storage_type == "Ubuntu Share":
        location = f"{host_ip}:{disk_path}"
    if storage_type == "Synology NAS" and disk_file_system.startswith("//"):
            # CIFS mount looking like "//HOST_IP/disk_path"
            split = disk_file_system.lstrip('/').split("/")
            location = f"{split[0]}:/{'/'.join(split[1:])}"
    # Ensure trailing "/"
    return location.rstrip("/") + "/"


def create_progressbar(percentage, color):
    if percentage is None:
        value = 10
        displayed_value = "?"
    else:
        value = round(percentage)
        displayed_value = f"{value}%"
    return f"""<div class="progress" style="height: 26px;">
    <div class="progress-bar bg-{color}" role="progressbar" 
       style="width: {value}%;" aria-valuenow="{value}" aria-valuemin="0" aria-valuemax="100">
       <span>{displayed_value}</span></div>
    </div>"""


def get_network_rate_in_kbits(value):
    # By default, network rate in bits/s
    if value is None:
        return value
    return value / 1024


def get_network_rate_color(network_rate):
    if network_rate is None:
        return "secondary"  # Gray (unknown)
    elif network_rate < LOW_NET_RATE:
        return "primary"  # Blue (low / idle)
    elif network_rate < MEDIUM_NET_RATE:
        return "success"  # Green (medium)
    elif network_rate < HIGH_NET_RATE:
        return "warning"  # Yellow (high)
    else:
        return "danger"  # Red (very high / critical)


def get_uptime_color(uptime):
    if uptime is None:
        return "secondary"  # Gray (unknown)
    elif uptime < LOW_UPTIME:
        return "primary"  # Blue (low / idle)
    elif uptime < MEDIUM_UPTIME:
        return "success"  # Green (medium)
    elif uptime < HIGH_UPTIME:
        return "warning"  # Yellow (high)
    else:
        return "danger"  # Red (very high / critical)


def get_readable_usage_memo(value):
    if value is None:
        return value
    return html.escape(value)


def get_usage_memo_color(usage_memo):
    if usage_memo is None:
        return "secondary"  # Gray (unknown)
    if usage_memo.upper() in ["FREE", "IDLE"]:
        return "primary"  # Blue (low / idle)
    else:
        return "dark"  # Black


def create_html_foot_banner(data):
    return f"""
<div class="alert alert-secondary bb-foot-banner" role="alert">
    <u>Legend</u>:
    <table class="table table-secondary">
      <thead>
        <tr>
          <th scope="col">Metric</th>
          <th scope="col" class="text-primary">Low</small></th>
          <th scope="col" class="text-success">Medium</th>
          <th scope="col" class="text-warning">High</th>
          <th scope="col" class="text-danger">Very High</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Load average</strong> <small>(with regard to CPU(s))</small></td>
          <td class="text-primary">Below {LOW_LOAD_PERCENT}%</td>
          <td class="text-success">Between {LOW_LOAD_PERCENT}% and {MEDIUM_LOAD_PERCENT}%</td>
          <td class="text-warning">Between {MEDIUM_LOAD_PERCENT}% and {HIGH_LOAD_PERCENT}%</td>
          <td class="text-danger">Above {HIGH_LOAD_PERCENT}%</td>
        </tr>
        <tr>
          <td><strong>Used memory</strong></td>
          <td class="text-primary">Below {LOW_MEM_PERCENT}%</td>
          <td class="text-success">Between {LOW_MEM_PERCENT}% and {MEDIUM_MEM_PERCENT}%</td>
          <td class="text-warning">Between {MEDIUM_MEM_PERCENT}% and {HIGH_MEM_PERCENT}%</td>
          <td class="text-danger">Above {HIGH_MEM_PERCENT}%</td>
        </tr>
        <tr>
          <td><strong>Disk space usage</strong></td>
          <td class="text-primary">Below {LOW_SPACE_PERCENT}%</td>
          <td class="text-success">Between {LOW_SPACE_PERCENT}% and {MEDIUM_SPACE_PERCENT}%</td>
          <td class="text-warning">Between {MEDIUM_SPACE_PERCENT}% and {HIGH_SPACE_PRECENT}%</td>
          <td class="text-danger">Above {HIGH_SPACE_PRECENT}%</td>
        </tr>
        <tr>
          <td><strong>Network rate</strong> <small>(bits/second)</small></td>
          <td class="text-primary">Below {LOW_NET_RATE//1024}K</td>
          <td class="text-success">Between {LOW_NET_RATE//1024}K and {MEDIUM_NET_RATE//(1024*1024)}M</td>
          <td class="text-warning">Between {MEDIUM_NET_RATE//(1024*1024)}M and {HIGH_NET_RATE//(1024*1024)}M</td>
          <td class="text-danger">Above {HIGH_NET_RATE//(1024*1024)}M</td>
        </tr>
        <tr>
          <td><strong>Uptime</strong></td>
          <td class="text-primary">Below {LOW_UPTIME} day</td>
          <td class="text-success">Between {LOW_UPTIME} and {MEDIUM_UPTIME} days</td>
          <td class="text-warning">Between {MEDIUM_UPTIME} and {HIGH_UPTIME} days</td>
          <td class="text-danger">Above {HIGH_UPTIME} days</td>
        </tr>
      </tbody>
    </table>
</div>
"""


if __name__ == "__main__":
    # Handy command line interface (-h for help)
    import argparse

    parser = argparse.ArgumentParser(
        description="Run BigBrother server, serving a user-friendly view of the monitoring results")
    parser.add_argument('--host', default=DEFAULT_HOST,
                        help='Server host name (default: %(default)s)')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                        help='Server port number (default: %(default)s)')
    parser.add_argument('--data_json', metavar="PATH", default=DEFAULT_MONITORING_JSON_PATH,
                        help='Path to input JSON file (default: %(default)s)')
    parser.add_argument("--debug", action="store_true", default=False,
                        help="Debug mode, server restarting at each code change (default: %(default)s)")
    args = parser.parse_args()

    # Go
    run_server(
        host=args.host,
        port=args.port,
        data_json_path=args.data_json,
        debug=args.debug,
    )
