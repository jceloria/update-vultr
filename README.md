# Update A Vultr firewall rule with your current public IP

## Installation
This script can run anywhere with Python 3 installed that has a outbound internet connection. Configuration 
is done by copying and editing vultr.ini.example -> vultr.ini or by creating a new file w/ the following format:
```
[main]
# The base URL for the Vultr API
base_url = https://api.vultr.com/v2

# The API key used to authenticate requests
api_key = XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# The URL used to find our public IP address
public_ip_url = https://api.ipify.org

# tag: The tag (note) used to identify the firewall rule being updated
tag = MyIP

# The type of firewall IP rule (v4/v6)
ip_type = v4

# The protocol for the firewall rule to update (TCP/UDP only)
protocol = TCP

# This field can be a specific port or a colon separated port range
port = 22
```

The following options are available:
```
$─► ./update_vultr.py --help
usage: update_vultr.py [-h] [-L {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                       [-c CONFIG]

 Update Vultr API Settings

optional arguments:
  -h, --help            show this help message and exit
  -L {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the log level (default is INFO)
  -c CONFIG, --config CONFIG
                        Path to config file

```
