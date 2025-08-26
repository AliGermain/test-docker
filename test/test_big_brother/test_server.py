import os
import sys
import unittest
from bs4 import BeautifulSoup

TOP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
[sys.path.append(dir_path) for dir_path in [TOP_DIR] if dir_path not in sys.path]

from big_brother.run_server import create_html_page
from big_brother.details.utils import load_json


class BBMServer(unittest.TestCase):
    def test_create_html_page(self):
        # Check input
        json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "monitoring_results_sample.json"))
        self.assertTrue(os.path.isfile(json_path))
        data = load_json(json_path)

        # Create HTML page
        html_page = create_html_page(data, "BigBrother")
        self.assertTrue(html_page.strip().startswith("<!doctype html>"))

        # Check HTML with BeautifulSoup
        soup = BeautifulSoup(html_page, 'html.parser')
        # -- Title
        self.assertEqual(soup.title.string, "BigBrother")

        # -- Head banner
        header = soup.body.find("div", {"class": "bb-head-banner"})
        self.assertTrue(header is not None)
        self.assertTrue(header.text.strip().startswith("Last update: 2022-12-16 13:44:43 ("))

        # -- Instances table
        table = soup.body.find("table", {"class": "bb-instances-table"})
        self.assertTrue(table is not None)
        # ---- Header
        cell_values = [x.text for x in table.thead.find_all("th")]
        expected_values = ['Instance', 'Load Average', 'Memory',
                           'Home Disk Space', 'Net. Rate (b/s)', 'Uptime', 'Usage Memo',
                           'Name', 'IP', 'CPU(s)', '1min', '5min', '15min', 'Total',
                           'Used', 'Usage', 'Total', 'Used', 'Usage', 'Sent', 'Received', 'Days',
                           '/opt/bigbrother.memo']
        self.assertListEqual(cell_values, expected_values)
        # ---- Content rows
        rows = table.tbody.find_all("tr")
        self.assertEqual(len(rows), 3)
        # ---- Row 0
        cell_values = [x.text.strip() for x in rows[0].find_all("td")]
        expected_values = ['apollo-1', '192.168.10.101', '80', '142.35', '116.50', '110.00',
                           '504G', '172G', '34%', '7.2T', '1.7T', '23%', '64K', '1.0M', '148', 'TCu 🛰️+Landsat']
        self.assertListEqual(cell_values, expected_values)
        # ---- Row 1
        cell_values = [x.text.strip() for x in rows[1].find_all("td")]
        expected_values = ['helios', '192.168.10.107', '12', '0.65', '0.51', '0.32',
                           '126G', '8.6G', '7%', '913G', '356G', '39%', '2K', '1K', '0', 'MK 🖥️']
        self.assertListEqual(cell_values, expected_values)
        # ---- Row 2
        cell_values = [x.text.strip() for x in rows[2].find_all("td")]
        expected_values = ['scoubi', '192.168.10.123', 'None', 'None', 'None',
                           'None', 'None', 'None', '?', 'None', 'None', '?', 'None', 'None', 'None', 'None']
        self.assertListEqual(cell_values, expected_values)

        # -- Storages table
        table = soup.body.find("table", {"class": "bb-storages-table"})
        self.assertTrue(table is not None)
        # ---- Header
        cell_values = [x.text for x in table.thead.find_all("th")]
        expected_values = ['Storage', 'Space', 'Name', 'Type', 'Location', 'Total', 'Used', 'Usage']
        self.assertListEqual(cell_values, expected_values)
        # ---- Content rows
        rows = table.tbody.find_all("tr")
        self.assertEqual(len(rows), 2)
        # ---- Row 0
        cell_values = [x.text.strip() for x in rows[0].find_all("td")]
        expected_values = ['datacenter', 'Synology NAS', '192.168.10.206:/datacenter/', '77T', '63T', '82%']
        self.assertListEqual(cell_values, expected_values)
        # ---- Row 1
        cell_values = [x.text.strip() for x in rows[1].find_all("td")]
        expected_values = ['datagri', 'NetApp NAS', '192.168.10.225:/agri/', '6.7T', '5.1T', '76%']
        self.assertListEqual(cell_values, expected_values)

        # -- Foot banner
        footer = soup.body.find("div", {"class": "bb-foot-banner"})
        self.assertTrue(footer is not None)
        self.assertEqual(footer.u.text, "Legend")


if __name__ == '__main__':
    unittest.main()
