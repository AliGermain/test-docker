import os


PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DEFAULT_INSTANCES_JSON_PATH = os.path.join(PROJECT_DIR, "instances.json")
DEFAULT_MONITORING_JSON_PATH = os.path.join(PROJECT_DIR, "live_data", "monitoring_results.json")
DEFAULT_MONITOR_LOG_PATH = os.path.join(PROJECT_DIR, "live_data", "monitor.log")
DEFAULT_MONITOR_PERIOD = 10  # 10s

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

USAGE_MEMO_PATH = "/opt/bigbrother.memo"


class MainProp:
    """Enumeration-like definition of main properties in monitoring results"""
    METADATA = "metadata"
    INSTANCES = "instances"
    STORAGES = "storages"


class MetaProp:
    """Enumeration-like definition of JSON metadata properties in monitoring results"""
    PROCESS_TIMESTAMP = "timestamp"
    PROCESS_TIMEDELTA = "timedelta"


class InstanceProp:
    """Enumeration-like definition of instance properties in monitoring results"""
    NAME = "name"
    TYPE = "type"
    IP = "ip"
    USER = "user"
    NET_INTERFACE = "net_interface"
    CPU_COUNT = "cpu"
    LOAD_AVERAGE_1 = "load_avg_1"
    LOAD_AVERAGE_5 = "load_avg_5"
    LOAD_AVERAGE_15 = "load_avg_15"
    MEMORY_TOTAL = "mem_total"
    MEMORY_USED = "mem_used"
    DISK_PATH = "disk_path"
    DISK_FILE_SYSTEM = "disk_file_sys"
    DISK_SPACE_TOTAL = "disk_space_total"
    DISK_SPACE_USED = "disk_space_used"
    DISK_SPACE_AVAILABLE = "disk_space_avail"
    NET_SEND_RATE = "net_send_rate"
    NET_RECEIVE_RATE = "net_receive_rate"
    UPTIME = "uptime"
    USAGE_MEMO = "usage_memo"
