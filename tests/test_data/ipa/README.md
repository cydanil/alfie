# icepap-ipassign

Remotely configure IcePAP network settings.

IPAssign is a tool developed within ESRF's DEG (Detector and Electronics Group).
Its aim is to provide an easy way to set-up network settings over UDP multicast,
without the need for a complete DaNCE suite.

![alt text](ipa_gui/action_shot.png "Action shot")

## Installing

This package requires Python 3.7+, and is available on pypi:

    pip install icepap-ipassign

## Usage

ipassign is a graphical application.
Launch it so:

    $ ipassign

In the main window, you will be given a list of discovered devices. Clicking on one
will show its configuration window.

The most common operation is the setting of the hostname, and a simple window will
pop up.  
For further network settings, hit `Advanced`.

The gui is further documented in [ipa_gui/gui.md](ipa_gui/gui.md)

## Protocol

### Messaging

ipassign uses UDP multicast on `225.0.0.37` port `12345`.  

There are three types of message: discovery, configurations, and acknowledgements.

Discovery messages are sent by ipassing to list all devices on the network.  

Configurations messages are either devices sending their configurations, or
ipassing sending a new configuration to a device.  

Acknowledgements are sent by a device upon applying a new configuration.  
These are not sent if the device was requested to reboot.


A typical exchange of information has the following format:

    [ipassign] who's there? discovery packet
    [icepap 1] me, my mac address is 00:... and my configuration is ...
    [icepap 2] me, my mac address is 01:... and my configuration is ...
    [ipassign] device with mac 01:... , please apply the following configuration: ...
               and reboot/apply now dynamically/write to flash.
    [icepap 2] okay, here's an ack message, with my status code following your request.
    [ipassign] who's there? discovery packet

For demonstration purposes, a simple listener is available in `utils/listener.py` and can be invoked so:

```bash
$ ipassign-listener

Waiting for messages...
```

Messages seen in the multicast group will then be displayed in human readable format.

### Packet Format

An IPAssign packet has the following structure:

    [header]      # 14 bytes
    [destination] # 6 bytes, 6 x uint8
    [payload]     # variable length, 0 to 1024 bytes
    [checksum]    # 4 bytes, uint32, little endian

- `[destination]` is the mac address of the target device. When broadcasting,
                  this address is set to a single byte with value 0x00.
- `[payload]` is the data sent to the target device.
- `[checksum]` the crc32 of `[header][destination][payload]`, encoded in little
               endian, then appended to the packet.
- `[header]` has the following structure:

        [source]        # 6 bytes, 6 x uint8
        [target count]  # 2 byte, uint16
        [packet number] # 2 bytes, uint16
        [command]       # 2 bytes, uint16
        [payload size]  # 2 bytes, uint16

  - `[source]` is the mac address of the device emitting the packet.
  - `[target count]` is set to 0 when broadcasting to the whole group,
                     or 1 when targeting a specific device.
  - `[packet number]` is the packet count sent by this device.
  - `[command]` is one of the predefined commands, eg. set hostname, see
                `ipassign.commands` for available commands.
  - `[payload size]` describes the quantity of bytes in the payload to read.

---

`target count` is called so, to maintain consistency with other legacy code.  
It was originally envisioned that several devices could be targeted by a single
message, hence its uint16 format.   
In practice, however, it is effectively used as a boolean: it should be
understood as `is_not_broadcasting`. 

---


### Discovery Messages

Here is the anatomy of a discovery message:

    0x78 0x45 0xC4 0xF7 0x8F 0x48   # mac
    0x00 0x00                       # target count (broadcast to group)
    0x00 0x01                       # packet number
    0x00 0x02                       # command (request for parameters)
    0x00 0x00                       # payload length
    0x00                            # destination mac, truncated to 1 byte.
    0x31 0x8F 0x64 0x48             # checksum

Incidentally, for its lack of payload, it is the smallest message that can be sent.

### Configuration Payload

A configuration is either a device's current network configuration, or one it should apply.
The payload has the following structure:

    [icepap id]    # 6 bytes, 6 x uint8
    [ip address]   # 4 bytes, uint32, little endian
    [broadcast]    # ditto
    [netmask]      # ditto
    [gateway]      # ditto
    [mac address]  # 6 bytes, 6 x uint8
    [flags]        # 2 bytes, uint32
    [hostname]     # variable length, 24 bytes max, ascii string

- `[icepap id]` is the mac address of the device providing or applying the config.
- `[ip address]` is this configuration's address.
- `[broadcast]` is this configuration's broadcast address.
- `[netmask]` is this configuration's netmask.
- `[gateway]` is this configuration's gateway address.
- `[mac address]` is this configuration's mac address.
- `[flags]` are the actions the device should do upon applying a new configuration.
- `[hostname]` is this configuration's hostname.

The device can be asked to perform one of three actions upon applying a new
configuration.
These are set in the `[flags]` field and are:

- reboot (first bit set);
- dynamically apply the changes (second bit set);
- write them to flash (third bit set).

Here is a configuration payload:

    0x00 0x0C 0xC6 0x69 0x13 0x2D                 # icepap id, a mac address
    0xAC 0x18 0x9B 0xDE 0xAC                      # IP address, 172.24.155.222
    0xAC 0x18 0x9B 0xDE 0xFF                      # broadcast, 172.24.155.255
    0xFF 0xFF 0xFF 0xFF 0x00                      # netmask, 255.255.255.0
    0xAC 0x18 0x9B 0xDE 0x63                      # gateway, 172.24.155.99
    0x00 0x0C 0xC6 0x69 0x13 0x2D                 # reprogrammable mac address
    0x00 0x00                                     # flags, none
    0X74 0X68 0X78 0X63 0X6F 0X72 0X6F 0X6E 0X61  # hostname

This message will be deserialised as follows:

```python
from ipassign import Message
msg  = b'\x00\x0c\xc6\x69\x13\x2d\x01\x00\x00\x00\x03\x00\x38\x00\x00\x22\x19\x06\xbf\x58\x00\x0c\xc6\x69\x13\x2d\xac\x18\x9b\xde\xac\x18\x9b\xff\xff\xff\xff\x00\xac\x18\x9b\x63\x00\x0c\xc6\x69\x13\x2d\x00\x00\x00\x00\x69\x63\x65\x65\x75\x34\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb3\x57\x23\x0d'

m = Message.from_bytes(msg)

print(m)
[header]
    [source]      = 00:0c:c6:69:13:2d
    [target id]   = 1
    [packet no]   = 0
    [command]     = SEND_CONFIG [0x3]
    [payload len] = 56
[destination] = 00:22:19:06:bf:58
[payload] = [configuration]
                [target id]   = 00:0c:c6:69:13:2d
                [ip address]  = 172.24.155.222
                [broadcast]   = 172.24.155.255
                [netmask]     = 255.255.255.0
                [gateway]     = 172.24.155.99
                [mac address] = 00:0c:c6:69:13:2d
                [flags]       =
                [hostname]    = iceeu4
[checksum] = 0xd2357b3
```

### Acknowledgment Payload

Whilst a device will send an acknowledgement after applying a new configuration,
if not told to reboot, it is up to the creator of said configuration to
validate it.

An acknowledgment payload has the following structure:

    [packet number] # 2 bytes, uint16
    [error code]    # 2 bytes, uint16

- `[packet number]` is the packet number referring to the acknowledge packet.
                    If a configuration packet was sent with packet number 5,
                    it is then possible to check that the settings match the ones
                    in the packet of that packet.
- `[error code]` is a status code of having applied the received settings.

Here is an acknowledgement payload:
```python
from ipassign import acknowledgements, Acknowledgement

payload = Acknowledgement(packno=5,
                          code=acknowledgements.OK)
```

This message would have the following hex representation:

    0x05 0x00  # Reply to the configuration received in sender's packet no. 5
    0x00 0x00  # Ok

This message would be represented as:

    [acknowledgement]
        [packet number] = 5
        [code]          = OK [0x0]

Error codes are defined in `ipassign.acknowledgements`.

## Testing and Development

Clone and download this repository, and install it with `pip`:

    pip install -e .

Testing this library done with `pytest`:

    pytest -vv

For development, a mock IcePAP server can be found in `utils/mock_icepap`.
This mock server behaves like real hardware, and will send the appropriate
replies:

```bash
$ python ipa_utils/mock_icepap
Working with e3:cd:77:a0:18:30 and dvepklrlyq, no ack: False
```

The script also accepts a mac address as argument:

```bash
$ python ipa_utils/mock_icepap 00:0B:AD:C0:FF:EE
Working with 00:0b:ad:c0:ff:ee and kqifwchhiz, no ack: False
```

It's also possible to make the script not send acknowledgements:

```bash
$ python ipa_utils/mock_icepap --nack
Working with 53:2e:d2:f9:7b:af and kvdkkleuqc, no ack: True
```



## Embedded IcePAP Considerations

The `listener` process embedded in IcePAP devices expects well-formatted
packets, and does not do any error handling.  
As such, it is up to the sender to ensure that the packet is correct.

Any malformed message or nonsense bytes sent to an IcePAP will make
the `listener` crash.

To restart it, telnet as `root` in the IcePAP device, and execute
`/usr/sbin/icepap_startup_local restart`:

```bash
$ telnet icepap
icepap login: root
Password:

root@icepap > /usr/sbin/icepap_startup_local restart
Stopping ipassign listener......done
Stopping icepap communication...done
Removing icepap driver..........done
Removing blisspipe driver.......done
Loading  icepap driver..........done
Loading  blisspipe driver.......done
Starting icepap communication...done
Starting ipassign listener......done
```

The device will then appear in `ipassign` upon doing a `Refresh`.

Sending a configuration without any command flags will do nothing.  
For a configuration to take effect, it should be applied dynamically and/or
written to flash.
