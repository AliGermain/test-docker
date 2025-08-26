import os
import subprocess
import sys
import unittest
import tempfile
import socket
import getpass
import datetime
import re

TOP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
[sys.path.append(dir_path) for dir_path in [TOP_DIR] if dir_path not in sys.path]

from big_brother.run_monitor import monitor_instances
from big_brother.details.utils import write_json, load_json


class BBMonitor(unittest.TestCase):
    def test_monitor_single_instance(self):
        with tempfile.TemporaryDirectory(prefix="test_monitor_") as tmp_dir:
            # Define tmp paths
            in_json_path = os.path.join(tmp_dir, "instances.json")
            out_json_path = os.path.join(tmp_dir, "results.json")

            # Create target instances JSON containing a 1 instance (the one running this test)
            # and one storage space (the home disk of the running instance)
            this_instance = {
                "name": socket.gethostname(),
                "ip": "localhost",
                "user": getpass.getuser(),
                "net_interface": get_active_net_interface(),
            }
            this_storage = {
                "name": "/home",
                "type": "Home Disk",
                "ip": "localhost",
                "user": getpass.getuser(),
                "disk_path": "/"
            }
            json_data = {
                "instances": [this_instance],
                "storages": [this_storage],
            }
            write_json(in_json_path, json_data)
            self.assertTrue(os.path.isfile(in_json_path))

            # Monitor this instance
            monitor_instances(in_json_path, out_json_path)
            self.assertTrue(os.path.isfile(out_json_path))

            # Check results
            results = load_json(out_json_path)
            # -- Existence
            self.assertTrue(results.get("metadata") is not None)
            self.assertTrue(results.get("instances") is not None)
            self.assertEqual(len(results.get("instances")), 1)
            self.assertTrue(results.get("storages") is not None)
            self.assertEqual(len(results.get("storages")), 1)
            # -- Metadata
            self.assertTrue(results["metadata"]["timestamp"].startswith(datetime.datetime.now().strftime("%Y-%m-%d")))
            self.assertTrue(results["metadata"]["timedelta"].startswith("0:00:0"))  # Should take less than 10s
            # -- Instance
            self.assertEqual(results["instances"][0]["name"], this_instance["name"])
            self.assertEqual(results["instances"][0]["ip"], this_instance["ip"])
            self.assertEqual(results["instances"][0]["user"], this_instance["user"])
            self.assertEqual(results["instances"][0]["net_interface"], this_instance["net_interface"])
            self.assertTrue(0 < int(results["instances"][0]["cpu"]))
            self.assertTrue(0 <= float(results["instances"][0]["load_avg_1"]))
            self.assertTrue(0 <= float(results["instances"][0]["load_avg_5"]))
            self.assertTrue(0 <= float(results["instances"][0]["load_avg_15"]))
            self.assertTrue(0 < int(results["instances"][0]["mem_total"]))
            self.assertTrue(0 < int(results["instances"][0]["mem_used"])
                            <= int(results["instances"][0]["mem_total"]))
            self.assertTrue(len(results["instances"][0]["disk_file_sys"]))
            self.assertTrue(0 < int(results["instances"][0]["disk_space_total"]))
            self.assertTrue(0 < int(results["instances"][0]["disk_space_used"])
                            <= int(results["instances"][0]["disk_space_total"]))
            self.assertTrue(0 <= int(results["instances"][0]["net_send_rate"]))
            self.assertTrue(0 <= int(results["instances"][0]["net_receive_rate"]))
            self.assertTrue(len(str(results["instances"][0]["usage_memo"])))
            # -- Storage
            self.assertEqual(results["storages"][0]["name"], this_storage["name"])
            self.assertEqual(results["storages"][0]["type"], this_storage["type"])
            self.assertEqual(results["storages"][0]["ip"], this_storage["ip"])
            self.assertEqual(results["storages"][0]["user"], this_storage["user"])
            self.assertEqual(results["storages"][0]["disk_path"], this_storage["disk_path"])
            self.assertTrue(len(results["storages"][0]["disk_file_sys"]))
            self.assertTrue(0 < int(results["storages"][0]["disk_space_total"]))
            self.assertTrue(0 < int(results["storages"][0]["disk_space_used"])
                            <= int(results["storages"][0]["disk_space_total"]))


def get_active_net_interface():
    cmd_output = subprocess.run("ip a", shell=True, capture_output=True)
    if cmd_output.returncode == 0:
        lines = cmd_output.stdout.decode().strip().split("\n")
        for line in lines:
            # Find line with "state UP", and return associated net interface name (ex below: "ens4")
            # 2: ens4: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
            regex_result = re.match(r'\d+: (\w+): .* state UP .*', line)
            if regex_result:
                return regex_result.group(1)
    return None


if __name__ == '__main__':
    unittest.main()
