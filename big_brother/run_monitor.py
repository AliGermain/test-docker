import os
import sys
import subprocess
import re
import time
import datetime

TOP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
[sys.path.append(dir_path) for dir_path in [TOP_DIR] if dir_path not in sys.path]

from big_brother.details.globals import MainProp, MetaProp, InstanceProp, DEFAULT_INSTANCES_JSON_PATH, \
    DEFAULT_MONITORING_JSON_PATH, DEFAULT_MONITOR_PERIOD, DEFAULT_MONITOR_LOG_PATH, DATETIME_FORMAT, USAGE_MEMO_PATH
from big_brother.details.logger import create_rotating_logger
from big_brother.details.utils import load_json, write_json


SSH_TIMEOUT = 10
LOCALHOST_IPS = ["localhost", "127.0.0.1"]


def monitor_instances_periodically(instances_json_path, out_json_path, log_path, period):
    # Logger
    logger = create_rotating_logger(log_path=log_path, log_name="BBMonitor")
    # Period checkpoint
    if period <= 0:
        raise RuntimeError(f"Invalid period: {period}")
    # On repeat...
    while True:
        # Monitor
        monitor_instances(
            instances_json_path=instances_json_path,
            out_json_path=out_json_path,
            logger=logger,
        )
        # Wait
        logger.info("-" * 80)
        logger.info(f"Sleep {period}s...")
        time.sleep(period)
        logger.info("-" * 80)


def monitor_instances(instances_json_path, out_json_path, logger=None):
    # Logger
    if logger is None:
        # -- Dummy logger
        logger = create_rotating_logger(log_path=None, no_console_log=True, log_name="BBMonitor")
    try:
        # Init timing
        start_time = time.time()
        # Load instance and storage details
        json_data = load_json(instances_json_path)
        # Monitor each instance
        instances = json_data.get("instances")
        instance_results = []
        logger.info(f"Monitor {len(instances)} instances")
        for i, instance in enumerate(instances, start=1):
            name = instance[InstanceProp.NAME]
            ip = instance[InstanceProp.IP]
            ssh_user = instance[InstanceProp.USER]
            home_disk_path = "/"
            net_interface = instance[InstanceProp.NET_INTERFACE]
            logger.info(f"[{i}/{len(instances)}] {name} ({ip})")
            result = instance.copy()
            result.update(get_nproc_metrics(ip, ssh_user, logger))
            result.update(get_top_metrics(ip, ssh_user, logger))
            result.update(get_free_metrics(ip, ssh_user, logger))
            result.update(get_df_metrics(ip, home_disk_path, ssh_user, logger))
            result.update(get_iftop_metrics(ip, net_interface, ssh_user, logger))
            result.update(get_uptime_metrics(ip, ssh_user, logger))
            result.update(get_usage_memo(ip, ssh_user, logger))
            logger.info(f">> {result}")
            instance_results.append(result)
        # Monitor each storage
        storages = json_data.get("storages")
        storage_results = []
        logger.info(f"Monitor {len(storages)} storages")
        for i, storage in enumerate(storages, start=1):
            name = storage[InstanceProp.NAME]
            ip = storage[InstanceProp.IP]
            ssh_user = storage[InstanceProp.USER]
            disk_path = storage[InstanceProp.DISK_PATH]
            logger.info(f"[{i}/{len(storages)}] {name} ({ip} - {disk_path})")
            result = storage.copy()
            result.update(get_df_metrics(ip, disk_path, ssh_user, logger))
            logger.info(f">> {result}")
            storage_results.append(result)
        # Add metadata
        logger.info(f"Generate metadata")
        metadata = generate_metadata(start_time)
        logger.info(f">> {metadata}")
        final_results = {
            MainProp.METADATA: metadata,
            MainProp.INSTANCES: instance_results,
            MainProp.STORAGES: storage_results,
        }
        # Write results
        logger.info(f"Write in JSON")
        write_json(out_json_path, final_results)
    except Exception as e:
        logger.exception(e)
        raise


def wrap_command_for_remote_ip(cmd, ip, ssh_user=None):
    if ip in LOCALHOST_IPS:
        # Localhost, no need to use ssh
        return cmd
    else:
        # Remote instance, Send command though ssh
        if ssh_user is None:
            ssh_dst = f"{ip}"
        else:
            ssh_dst = f"{ssh_user}@{ip}"
        return f"timeout {SSH_TIMEOUT} ssh {ssh_dst} {cmd}"


def get_nproc_metrics(ip, ssh_user, logger):
    """Get cpu count with nproc command

    Raw command output example:
    80
    """
    # Launch command, typically through ssh
    cmd = "nproc"
    cmd_line = wrap_command_for_remote_ip(cmd, ip, ssh_user)
    cmd_output = subprocess.run(cmd_line, shell=True, capture_output=True)
    # Process command output
    result = {InstanceProp.CPU_COUNT: None}
    if cmd_output.returncode == 0:
        # Success
        raw_lines = cmd_output.stdout.decode().strip().split("\n")
        # -- Extract metric from first and only line
        regex_result = re.match(r'(\d+)', raw_lines[0])
        if regex_result:
            result.update({InstanceProp.CPU_COUNT: int(regex_result.group(1))})
        else:
            logger.error(f"Regex search failed on '{raw_lines[0]}'")
    elif cmd_output.returncode == 124:
        # Timeout
        logger.error(f"Timeout running command '{cmd_line}'")
    else:
        # Fail
        logger.error(f"Error running command '{cmd_line}' :\n{cmd_output.stderr.decode().strip()}")
    return result


def get_top_metrics(ip, ssh_user, logger):
    """Get load_average metrics with top command

    Raw command output example:
    top - 09:20:25 up 3 days,  1:58,  0 users,  load average: 12,09, 12,26, 15,26
    Tasks: 809 total,  11 running, 798 sleeping,   0 stopped,   0 zombie
    %Cpu(s):  8,9 us,  4,0 sy,  0,0 ni, 85,8 id,  1,3 wa,  0,0 hi,  0,0 si,  0,0 st
    MiB Mem : 515841,1 total, 217901,8 free,   3527,2 used, 294412,1 buff/cache
    MiB Swap:   8192,0 total,   8065,0 free,    127,0 used. 508643,3 avail Mem

        PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
    1192587 rdteam    20   0  435708 152208  57388 R 100,0   0,0   0:28.52 otbAppl+
    1192611 rdteam    20   0  435708 142424  57372 R 100,0   0,0   0:26.68 otbAppl+
    1192626 rdteam    20   0  436392 140812  57528 R 100,0   0,0   0:25.27 otbAppl+
    1192691 rdteam    20   0  435700 136532  57556 R 100,0   0,0   0:21.75 otbAppl+
    """
    # Launch command, typically through ssh
    cmd = "top -b -n1 -i"
    cmd_line = wrap_command_for_remote_ip(cmd, ip, ssh_user)
    cmd_output = subprocess.run(cmd_line, shell=True, capture_output=True)
    # Process command output
    result = {
        InstanceProp.LOAD_AVERAGE_1: None,
        InstanceProp.LOAD_AVERAGE_5: None,
        InstanceProp.LOAD_AVERAGE_15: None,
    }
    if cmd_output.returncode == 0:
        # Success
        raw_lines = cmd_output.stdout.decode().strip().split("\n")
        # -- Extract metrics from 1st line
        regex_result = re.search(r'load average: (.+), (.+), (.+)', raw_lines[0])
        if regex_result:
            values = []
            for value in [regex_result.group(1), regex_result.group(2), regex_result.group(3)]:
                values.append(float(value.replace(",", ".")))
            result.update({
                InstanceProp.LOAD_AVERAGE_1: values[0],
                InstanceProp.LOAD_AVERAGE_5: values[1],
                InstanceProp.LOAD_AVERAGE_15: values[2],
            })
        else:
            logger.error(f"Regex search failed on '{raw_lines[0]}'")
    elif cmd_output.returncode == 124:
        # Timeout
        logger.error(f"Timeout running command '{cmd_line}'")
    else:
        # Fail
        logger.error(f"Error running command '{cmd_line}' :\n{cmd_output.stderr.decode().strip()}")
    return result


def get_free_metrics(ip, ssh_user, logger):
    """Get memory usage (RAM) metrics with free command

    Raw command output example:
    total        used        free      shared  buff/cache   available
    Mem:       528221324     2856272   308751440        5476   216613612   521607216
    Swap:        8388604      130048     8258556
    """
    # Launch command, typically through ssh
    cmd = "free"
    cmd_line = wrap_command_for_remote_ip(cmd, ip, ssh_user)
    cmd_output = subprocess.run(cmd_line, shell=True, capture_output=True)
    # Process command output
    result = {
        InstanceProp.MEMORY_TOTAL: None,
        InstanceProp.MEMORY_USED: None,
    }
    if cmd_output.returncode == 0:
        # Success
        raw_lines = cmd_output.stdout.decode().strip().split("\n")
        # -- Extract metrics from 2nd line
        regex_result = re.match(r'Mem:\s+(\d+)\s+(\d+)', raw_lines[1])
        if regex_result:
            result.update({
                InstanceProp.MEMORY_TOTAL: int(regex_result.group(1)),
                InstanceProp.MEMORY_USED: int(regex_result.group(2)),
            })
        else:
            logger.error(f"Regex search failed on '{raw_lines[1]}'")
    elif cmd_output.returncode == 124:
        # Timeout
        logger.error(f"Timeout running command '{cmd_line}'")
    else:
        # Fail
        logger.error(f"Error running command '{cmd_line}' :\n{cmd_output.stderr.decode().strip()}")
    return result


def get_df_metrics(ip, disk_path, ssh_user, logger):
    """Get disk space usage metrics with df command

    Raw command output example:
    Filesystem                        1K-blocks     Used Available Use% Mounted on
    /dev/mapper/ubuntu--vg-ubuntu--lv 957150424 24655784 883800368   3% /
    """
    # Launch command, typically through ssh
    cmd = f"df {disk_path}"
    cmd_line = wrap_command_for_remote_ip(cmd, ip, ssh_user)
    cmd_output = subprocess.run(cmd_line, shell=True, capture_output=True)
    # Process command output
    result = {
        InstanceProp.DISK_FILE_SYSTEM: None,
        InstanceProp.DISK_SPACE_TOTAL: None,
        InstanceProp.DISK_SPACE_USED: None,
        InstanceProp.DISK_SPACE_AVAILABLE: None,
    }
    if cmd_output.returncode == 0:
        # Success
        raw_lines = cmd_output.stdout.decode().strip().split("\n")
        # -- Extract metrics from 2nd line
        regex_result = re.match(r'(\S+)\s+(\d+)\s*(\d+)\s*(\d+)\s*(\d+)%', raw_lines[1])
        if regex_result:
            result.update({
                InstanceProp.DISK_FILE_SYSTEM: regex_result.group(1),
                InstanceProp.DISK_SPACE_TOTAL: int(regex_result.group(2)),
                InstanceProp.DISK_SPACE_USED: int(regex_result.group(3)),
                InstanceProp.DISK_SPACE_AVAILABLE: int(regex_result.group(4)),
            })
        else:
            logger.error(f"Regex search failed on '{raw_lines[1]}'")
    elif cmd_output.returncode == 124:
        # Timeout
        logger.error(f"Timeout running command '{cmd_line}'")
    else:
        # Fail
        logger.error(f"Error running command '{cmd_line}' :\n{cmd_output.stderr.decode().strip()}")
    return result


def get_iftop_metrics(ip, interface, ssh_user, logger):
    """Get network usage metrics through given interface with iftop command

    Raw command output example:
    interface: ens4
    IP address is: 192.168.10.107
    MAC address is: 04:d9:f5:13:8e:e1
    Listening on ens4
       # Host name (port/service if enabled)            last 2s   last 10s   last 40s cumulative
    --------------------------------------------------------------------------------------------
       1 192.168.10.107                           =>     13,0Kb     13,0Kb     13,0Kb     3,25KB
         192.168.10.205                           <=     40,4Kb     40,4Kb     40,4Kb     10,1KB
       2 239.255.255.250                          =>         0b         0b         0b         0B
         192.168.10.45                            <=       812b       812b       812b       203B
    --------------------------------------------------------------------------------------------
    Total send rate:                                     13,0Kb     13,0Kb     13,0Kb
    Total receive rate:                                  41,2Kb     41,2Kb     41,2Kb
    Total send and receive rate:                         54,2Kb     54,2Kb     54,2Kb
    --------------------------------------------------------------------------------------------
    Peak rate (sent/received/total):                     13,0Kb     41,1Kb     54,1Kb
    Cumulative (sent/received/total):                    3,25KB     10,3KB     13,5KB
    ============================================================================================
    """
    # Launch command, typically through ssh
    cmd = f"iftop -i {interface} -n -t -s 1"
    cmd_line = wrap_command_for_remote_ip(cmd, ip, ssh_user)
    cmd_output = subprocess.run(cmd_line, shell=True, capture_output=True)
    # Process command output
    result = {
        InstanceProp.NET_SEND_RATE: None,
        InstanceProp.NET_RECEIVE_RATE: None,
    }
    if cmd_output.returncode == 0:
        # Success
        raw_lines = cmd_output.stdout.decode().strip().split("\n")
        target_lines = "\n".join(raw_lines[-7:-5])
        # -- Extract metrics from 2nd line
        regex_result = re.match(r'Total send rate:\s+(\S+).*\nTotal receive rate:\s+(\S+)', target_lines)
        if regex_result:
            try:
                # Get rates in bits/s
                result.update({
                    InstanceProp.NET_SEND_RATE: convert_iftop_rate_to_bits(regex_result.group(1)),
                    InstanceProp.NET_RECEIVE_RATE: convert_iftop_rate_to_bits(regex_result.group(2)),
                })
            except Exception as e:
                logger.exception(e)
        else:
            logger.error(f"Regex search failed on '{target_lines}'")
    elif cmd_output.returncode == 124:
        # Timeout
        logger.error(f"Timeout running command '{cmd_line}'")
    else:
        # Fail
        logger.error(f"Error running command '{cmd_line}' :\n{cmd_output.stderr.decode().strip()}")
    return result


def get_uptime_metrics(ip, ssh_user, logger):
    """Get uptime

    Raw command output example:
    up 2 weeks, 4 days, 11 hours, 58 minutes
    """
    # Launch command, typically through ssh
    cmd = "uptime --pretty"
    cmd_line = wrap_command_for_remote_ip(cmd, ip, ssh_user)
    cmd_output = subprocess.run(cmd_line, shell=True, capture_output=True)
    # Process command output
    result = {InstanceProp.UPTIME: None}
    if cmd_output.returncode == 0:
        # Success
        raw_lines = cmd_output.stdout.decode().strip().split("\n")
        # -- Extract metric from first and only line
        regex_result = re.match(r'up (\d+ .*)', raw_lines[0])
        if regex_result:
            uptime_days = 0
            for item in regex_result.group(1).split(","):
                item_split = item.strip().split(" ")
                if len(item_split) != 2:
                    logger.error(f"Unexpected item '{item}' in '{raw_lines[0]}'")
                    uptime_days = None
                    break
                value, unit = int(item_split[0]), item_split[1]
                if unit in ["week", "weeks"]:
                    uptime_days += int(value) * 7
                elif unit in ["day", "days"]:
                    uptime_days += int(value)
                elif unit in ["hour", "hours", "minute", "minutes"]:
                    pass
                else:
                    logger.error(f"Unexpected unit '{unit}' in '{raw_lines[0]}'")
                    uptime_days = None
                    break
            result.update({InstanceProp.UPTIME: uptime_days})
        else:
            logger.error(f"Regex search failed on '{raw_lines[0]}'")
    elif cmd_output.returncode == 124:
        # Timeout
        logger.error(f"Timeout running command '{cmd_line}'")
    else:
        # Fail
        logger.error(f"Error running command '{cmd_line}' :\n{cmd_output.stderr.decode().strip()}")
    return result


def get_usage_memo(ip, ssh_user, logger):
    """Get usage memo text from USAGE_MEMO_PATH

    Raw command output example:
    MK
    """
    # Launch command, typically through ssh
    cmd = f"cat {USAGE_MEMO_PATH}"
    cmd_line = wrap_command_for_remote_ip(cmd, ip, ssh_user)
    cmd_output = subprocess.run(cmd_line, shell=True, capture_output=True)
    # Process command output
    result = {InstanceProp.USAGE_MEMO: None}
    if cmd_output.returncode == 0:
        # Success
        text = cmd_output.stdout.decode().strip()
        result.update({InstanceProp.USAGE_MEMO: text})
    elif cmd_output.returncode == 124:
        # Timeout
        logger.error(f"Timeout running command '{cmd_line}'")
    else:
        # Fail
        logger.error(f"Error running command '{cmd_line}' :\n{cmd_output.stderr.decode().strip()}")
    return result


def convert_iftop_rate_to_bits(rate_str):
    # Remove trailing "b" standing for bits
    if not rate_str.endswith("b"):
        raise RuntimeError("Expecting value in bits")
    rate_str = rate_str[:-1]
    # Ensure decimal separator is "."
    rate_str = rate_str.replace(",", ".")
    # Determine factor
    if rate_str.isnumeric():
        rate_float = float(rate_str)
    elif rate_str.endswith("K"):
        rate_float = float(rate_str[:-1]) * 1024
    elif rate_str.endswith("M"):
        rate_float = float(rate_str[:-1]) * 1024 * 1024
    elif rate_str.endswith("G"):
        rate_float = float(rate_str[:-1]) * 1024 * 1024 * 1024
    elif rate_str.endswith("T"):
        rate_float = float(rate_str[:-1]) * 1024 * 1024 * 1024 * 1024
    else:
        raise NotImplementedError("Not supporting network rate > Tb")
    # To integer
    return round(rate_float)


def generate_metadata(start_time):
    timestamp = datetime.datetime.now().strftime(DATETIME_FORMAT)
    process_time = datetime.timedelta(seconds=round(time.time() - start_time))
    return {
        MetaProp.PROCESS_TIMESTAMP: str(timestamp),
        MetaProp.PROCESS_TIMEDELTA: str(process_time),
    }


if __name__ == "__main__":
    # Handy command line interface (-h for help)
    import argparse

    parser = argparse.ArgumentParser(
        description="Launch BigBrother monitor, periodically retrieving metrics on targeted instances and storages")
    parser.add_argument('--instances_json', metavar="PATH", default=DEFAULT_INSTANCES_JSON_PATH,
                        help='Path to JSON file listing target instances and storages (default: %(default)s)')
    parser.add_argument('--out_json', metavar="PATH", default=DEFAULT_MONITORING_JSON_PATH,
                        help='Path to output JSON file where to store monitoring results (default: %(default)s)')
    parser.add_argument('--log', metavar="PATH", default=DEFAULT_MONITOR_LOG_PATH,
                        help='Path to log file (default: %(default)s)')
    parser.add_argument('--period', metavar="N", type=int, default=DEFAULT_MONITOR_PERIOD,
                        help='Repeat monitoring every N seconds (default: %(default)s)')
    args = parser.parse_args()

    # Go
    monitor_instances_periodically(
        instances_json_path=args.instances_json,
        out_json_path=args.out_json,
        log_path=args.log,
        period=args.period,
    )
