# Big Brother

![Static Badge](https://img.shields.io/badge/Tool-BigBrother-green)


## Description 

Monitor metrics of a bunch of instances and storages, and serve results as a local-network accessible web page.  
BigBrother is composed of two services: the **monitor** and the **server**.

### The Monitor

The **monitor** retrieve metrics for each targeted instance and storage, through shh.  
For example, `ssh rdteam@mercury nproc` returns the number of CPUs of `mercury`.

The targeted instances and storages are listed in an input JSON file (by default `big_brother/ìnstances.json`), 
detailing at least :
- The instance `name`
- The `ip` address and `user` to use for the ssh connection
- [Instance only] The `net_interface` to use for network metrics
- [Storage only] The `type` of storage (NAS, NetAPP, ...)

Example of input JSON file:
```json
{
   "instances": [
      {"name": "apollo-1", "ip": "192.168.10.101", "user": "rdteam", "net_interface": "eno50"},
      {"name": "helios", "ip": "192.168.10.107", "user": "rdteam", "net_interface": "ens4"},
      {"name": "mercury", "ip": "192.168.10.106", "user": "rdteam", "net_interface": "enp6s0"}
   ],
   "storages": [
      {"name": "datacenter", "type": "Synology NAS", "ip": "192.168.10.106", "user": "rdteam", "disk_path": "/home/rdteam/mnt/datacenter"},
      {"name": "projets", "type": "NetApp NAS", "ip": "192.168.10.106", "user": "rdteam", "disk_path": "/mnt/projets"}
     
   ]
}
```

The monitoring results are stored in an output JSON file (by default `big_brother/live_data/monitoring_results.json`), 
detailing for each instance and storage its input details as well as the retreived metrics (`cpu`, `load_avg_1`, ...). 

Example of output JSON file:
```json
{
   "metadata": {"timestamp": "2025-03-04 14:35:17", "timedelta": "0:04:18"},
   "instances": [
      {
         "name": "apollo-1", "ip": "192.168.10.101", "user": "rdteam", "net_interface": "eno50", "cpu": 80, 
         "load_avg_1": 151.96, "load_avg_5": 138.17, "load_avg_15": 126.0, 
         "mem_total": 528206460, "mem_used": 205361160, "disk_file_sys": "/dev/mapper/ubuntu--vg-ubuntu--lv", 
         "disk_space_total": 7747996276, "disk_space_used": 1414798800, "disk_space_avail": 5942644900, 
         "net_send_rate": 1095216660, "net_receive_rate": 220200960, "uptime": 148, 
         "usage_memo": "TCu \ud83d\udef0\ufe0f+Landsat"
      },
      {
         "name": "helios", "ip": "192.168.10.107", "user": "rdteam", "net_interface": "ens4", "cpu": 12,
         "load_avg_1": 0.64, "load_avg_5": 1.09, "load_avg_15": 0.96, 
         "mem_total": 131800368, "mem_used": 9559636, "disk_file_sys": "/dev/mapper/vgubuntu-root", 
         "disk_space_total": 957811888, "disk_space_used": 324921980, "disk_space_avail": 584162052, 
         "net_send_rate": 5028, "net_receive_rate": 5151, "uptime": 0, 
         "usage_memo": "MK \ud83d\udda5\ufe0f"
      },
      {
         "name": "mercury", "ip": "192.168.10.106", "user": "rdteam", "net_interface": "enp6s0", "cpu": 16,
         "load_avg_1": 0.0, "load_avg_5": 0.0, "load_avg_15": 0.0, 
         "mem_total": 131764444, "mem_used": 1903132, "disk_file_sys": "/dev/sdc2", 
         "disk_space_total": 503115808, "disk_space_used": 112723472, "disk_space_avail": 364761976,
         "net_send_rate": 0, "net_receive_rate": 208, "uptime": 28,
         "usage_memo": "Idle"
      }
   ],
   "storages": [
      {
         "name": "datacenter", "type": "Synology NAS", "ip": "192.168.10.106", "user": "rdteam",
         "disk_path": "/home/rdteam/mnt/datacenter", "disk_file_sys": "//192.168.10.206/datacenter",
         "disk_space_total": 82465199988, "disk_space_used": 67438837112, "disk_space_avail": 15026362876
      },
      {
         "name": "projets", "type": "NetApp NAS", "ip": "192.168.10.106", "user": "rdteam", 
         "disk_path": "/mnt/projets", "disk_file_sys": "192.168.10.225:/projets/", 
         "disk_space_total": 30601641984, "disk_space_used": 22277762048, "disk_space_avail": 8323879936
      }
   ]
}
```

The monitor repeats itself periodically (by default every 5 min).


### The Server

The **server** provides a user-friendly view of the monitoring results as a local-network accessible web page 
(by default http://192.168.10.132:1984/).

When the page is requested, the server loads the monitoring results stored in a JSON file 
(by default `big_brother/live_data/monitoring_results.json`), format them in an HTML page, and then send it back to the client.

Stack:
- [Bottle](https://bottlepy.org/docs/dev/#): a "fast, simple and lightweight WSGI micro web-framework for Python".
- [Paste](https://pythonpaste.readthedocs.io/en/latest/): multi-threaded server library
- [Bootstrap](https://getbootstrap.com/): a "Powerful, extensible, and feature-packed frontend toolkit".


## Installation

Follow the installation procedure of the top level `README.md`.

2 possibilities for the conda environement :
- Kerpy's generic environment : based on `rd-kerpy/requirements.txt` (see top level `README.md`.)
- BigBrother's specific environment (typically named `bb`) : based on `rd-kerpy/big_brother/requirements.txt`


## Usage

### [User] Consult BigBrother

To access BigBrother monitoring results, open http://192.168.10.132:1984/ with your favorite web browser 
from a Kermap workstation.


### [User] Book or free an instance

On each monitored instance, a `/opt/bigbrother.memo` text file is used to indicate who uses the instance.  
BigBrother displays the content of those files.
- To book an instance, edit its file with at least your initials (ex: `MK 🚜`). 
_If the instance is already used by someone, start by asking him permission previously._
- To indicated that an instance is free, put `Idle` or nothing in the file.


### [Maintenance] Relaunch BigBrother services

> **NOTE** : Considering an instance with BigBrother services already configured, 
> typically `drogon` (IP: `192.168.10.132`) with user `rdteam`

#### 1) Launch monitor

- Open a first screen (ex: `bb1`)
- Move in `rd-kerpy/big_brother` directory
- Activate `bb` (or `kerpy`) env
- [NEW] Launch new ssh agent and attach rdteam's bigbro SSH key to it
- Launch `run_monitor.py` (`-h` for help):
- Detach from screen
```commandline
rdteam@drogon:~$ screen -S bb1
rdteam@drogon:~$ cd src/rd-kerpy/
rdteam@drogon:/home/rdteam/src/rd-kerpy$ conda activate bb
(bb) rdteam@drogon:/home/rdteam/src/rd-kerpy$ eval "$(ssh-agent -s)"
(bb) rdteam@drogon:/home/rdteam/src/rd-kerpy$ ssh-add ~/.ssh/id_ed25519_BB
(bb) rdteam@drogon:/home/rdteam/src/rd-kerpy$ python big_brother/run_monitor.py 
```

#### 2) Launch server

- Open a second screen (ex: `bb2`)
- Move in `rd-kerpy/big_brother` directory
- Activate `bb` (or `kerpy`) env
- Launch `run_server.py` (`-h` for help):
  - *Hint: In dev/debug phase, use `--debug` to have the server restarting at each code change*
- Detach from screen
```commandline
rdteam@drogon:~$ screen -S bb2
rdteam@drogon:~$ cd src/rd-kerpy/
rdteam@drogon:/home/rdteam/src/rd-kerpy$ conda activate bb
(bb) rdteam@drogon:/home/rdteam/src/rd-kerpy$ python big_brother/run_server.py
```

## Running Tests

Launch all Kerpy tests with `kerpy` conda environment:
```
python test/run_all_tests.py
```

Launch only BigBrother tests with `bb` or `kerpy` conda environment:
```
python test/test_big_brother/test_monitor.py
python test/test_big_brother/test_server.py
```


## FAQ

#### How to monitor a new instance or a new storage?

Edit the `big_brother/instances.json` file with a new line for the target instance or storage.
- For an instance:
  - Example: `{"name": "hamilton", "ip": "192.168.10.110", "user": "rdteam", "net_interface": "enp3s0"}`
  - `user` : should be `rdteam`
  - `net_interface` : see below how to determine it
  
- For a storage:
  - Example: `{"name": "projets", "type": "NetApp NAS", "ip": "192.168.10.106", "user": "rdteam", "disk_path": "/mnt/projets"}`
  - `user` : should be `rdteam`
  - `ip` : IP of the instance mounting the volume, not of the volume itself (`192.168.10.106` = `mercury` in the example) 
  - `disk_path` : path to mounted volume (on an instance mounting it)

Then for a new instance : 
- If needed, setup the SSH pairing between bigbrother host and the target instance (see below)
  - Test from bigbrother host: `ssh rdteam@INSTANCE_IP nproc` should return a result without asking for a password
- If needed, create `/opt/bigbrother.memo` file (see below)
- If needed, install and configure it `iftop` (see below)


#### How to enable ssh access on an instance ?

On the target instance: 
```commandline
sudo apt install openssh-server -y
```

#### How to setup SSH key pairing for password-free monitoring

Initial setup on hosting instance (do it **once**), typically on `drogon` using `rdteam` user :
- Generate a single SSH key pair to be used with all monitored instances:
```
ssh-keygen -t ed25519 -C "rdteam.bigbrother@kermap.com" -f ~/.ssh/id_ed25519_BB
```
- Add SSH key to the ssh-agent  
If ssh-agent not already running, start it with `eval "$(ssh-agent -s)"`
```
ssh-add ~/.ssh/id_ed25519_BB
```

Initial setup for **each** monitored instance (repeat it for each new instance)
- Send SSH public key to the monitored instance :
```commandline
ssh-copy-id -i ~/.ssh/id_ed25519_BB rdteam@192.168.10.101
```


Pour le faire pour toutes les machinesd'un coup :
```
ansible-playbook \
  -i "apollo-1,apollo-2,apollo-3,apollo-5,apollo-6,apollo-7,apollo-8,aquila,bb8,bigmap,buzz,colombus,didymos,discovery,dracarys-1,drogon,hamilton,helios,hubble,kepler-1,kepler-2,mercator,mercury,R2D2,sagittarius,scoubi,spartan,sputnik,winterfell,Z840,Z840b," \
  -e ssh_key_path="/home/aconanec/projets/rd-kerpy/big_brother/playbook/cle.pub" \
  -e ssh_user="rdteam" \
  big_brother/playbook/add_key_to_machines.yml
```


#### How to determine the `net_interface` of an instance ?

On the target instance:
```commandline
ip a | grep "state UP"
```
Ex: `2: eno1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000` --> `eno1`

#### How to configure `iftop` on an instance ?

Install `iftop` and give permission to run it without `sudo`:
```commandline
sudo apt install iftop
sudo setcap cap_net_raw=eip $(which iftop)
```

#### How to create an editable `/opt/bigbrother.memo` file on an instance ?

```commandline
sudo touch /opt/bigbrother.memo
sudo chmod 777 /opt/bigbrother.memo
```
