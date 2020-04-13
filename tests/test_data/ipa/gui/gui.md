# IPAssign GUI

## Workflow

The usage of `ipassign` is as follows:

![alt text][gui_workflow]

There are four windows.  
`MainWindow` is the application entry point, on which a list of discovered
icepaps is displayed.  
There are two properties windows, a simpler `HostnameWindow` where the hostname
can be set, and a more advanced `NetworkWindow` in which ip setting can also be
configured. By default, `HostnameWindow` is displayed.  
`LogWindow` displays a log of the traffic on the network.

## MainWindow

This window is the user's entry point into the application.
It is responsible for discovery requests.
When launched, the application will send a discovery packet to find devices on
the network. This action can be repeated by clicking `Refresh`.  

Available devices are sorted by hostname in the central list.  
Clicking either on an entry in the list or on `Properties` will display its
properties.

## HostnameWindow

HostnameWindow only allows the setting of a device's hostname.  
Setting the hostname is the most common operation, and is ipassign's default
mode of operation.

The hostname is validated with respect to RFC 1123, section 2.1. If the
hostname is not valid, the `Apply` button is disabled.

The hostname will be written to flash and applied dynamically.

The `Advanced` push-button allows to switch to the `NetworkWindow` view.  

## NetworkWindow

NetworkWindow allows the setting of all of a device's network settings.

These are Hostname, IP settings, and whether to apply these settings
dynamically, to write them to flash, or reboot.

Alternatively, it is also possible to query the DNS and set these as values
to apply.

The configuration given at the moment of drawing the window is kept
within `self._config`. The new configuration will only be created when
`Apply` is clicked.

The `Reset` button resets the fields with the values previously obtained from
the device (passed to the window upon drawing), that is stored in `self._config`.

Within `NetworkWindow`, IP address fields are validated using
`ipaddress.IPv4Address`.  
As with `HostnameWindow`, the hostname is validated against RFC 1123.

If any field is invalid, `Apply` will be disabled.

Once `Apply` is clicked, IPs are verified to be in range of one another within
the netmask. If all is valid, then the configuration will be updated and sent
to the network via `NetworkInferface.send_configuration`.

Clicking `Simple Mode` switches back to `HostnameWindow`.

## Log Window

A log of the traffic on the network and actions within `ipassign` can be viewed
in `LogWindow`.
This window contains a read-only text field that, when displayed refreshes
automatically.  
From the log window, it is possible to save these to file.

## Networking

All the networking is handled by `networking.NetworkInterface`. This object has
the two methods `do_discovery` and `send_configuration`.
An instance is automatically created when importing the file, as a poor-man's
singleton.

Messages to and from `ipassign` always have the mac address `00:D1:5E:A5:ED:00`.

The socket times out on input messages after 200 ms. This was experimentally
chosen as a decent value. Perhaps a lesser value could work, but would create
issues in networks with more devices (eg. on awaiting configuration
acknowledgements).

[gui_workflow]: workflow.png "Image describing a user's workflow"
