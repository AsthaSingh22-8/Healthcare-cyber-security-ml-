
import pyshark

# Change 'Wi-Fi' to your network interface name if needed (use pyshark.tshark.tshark.get_tshark_interfaces() to list)
INTERFACE = 'Wi-Fi'

print(f"Starting live capture on interface: {INTERFACE}")

capture = pyshark.LiveCapture(interface=INTERFACE)

packet_limit = 10
count = 0

for packet in capture:
    try:
        print(f"Packet: {packet.sniff_time} | Protocols: {packet.highest_layer}")
        if 'IP' in packet:
            print(f"  From {packet.ip.src} to {packet.ip.dst}")
        if 'TCP' in packet:
            print(f"  TCP Port: {packet.tcp.srcport} -> {packet.tcp.dstport}")
        if 'UDP' in packet:
            print(f"  UDP Port: {packet.udp.srcport} -> {packet.udp.dstport}")
    except Exception as e:
        print(f"Error parsing packet: {e}")
    count += 1
    if count >= packet_limit:
        break

print("Live capture complete.")
