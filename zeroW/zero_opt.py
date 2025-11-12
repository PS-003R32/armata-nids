import scapy.all as scapy
import serial
import time
import numpy as np
import threading
import socket
from collections import defaultdict

PICO_SERIAL_PORT = '/dev/ttyACM0' # change this to your pico serial port ( type ls /dev/tty* to find it ) if yo are using UART RX/TX it woud be /dev/serial0 or similar.
SERIAL_BAUD = 115200 # change the baud rate if you modified it on the pico but this is the most reliable rate of transmission.
NETWORK_INTERFACE = "wlan0" # change this to your interface (e.g., "wlan0" or "eth0")
FLOW_TIMEOUT = 5.0

def get_host_ip(iface): # do not remov this function
    try:
        ip = scapy.get_if_addr(iface) 
        if ip:
            return ip
        else:
            raise Exception(f"Interface {iface} has no IP.")
    except Exception as e:
        print(f"Warning: Could not get IP for {iface} via scapy. {e}")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            print(f"Using default route IP: {ip}")
            return ip
        except Exception as e2:
            print(f"CRITICAL: Could not determine host IP. {e2}")
            print("Please set HOST_IP manually in the script.")
            return "127.0.0.1"

HOST_IP = get_host_ip(NETWORK_INTERFACE)
print(f"--- NIDS Sensor v2 ---")
print(f"Monitoring on interface: {NETWORK_INTERFACE}")
print(f"Host IP identified as: {HOST_IP}")
print(f"----------------------------------")

flow_data = defaultdict(dict)
serial_lock = threading.Lock()

try:
    pico_serial = serial.Serial(PICO_SERIAL_PORT, SERIAL_BAUD, timeout=1)
    print(f"Successfully opened serial port {PICO_SERIAL_PORT}")
except serial.SerialException as e:
    print(f"Error: Could not open serial port {PICO_SERIAL_PORT}. {e}")
    print("Please check the connection and port name.")
    exit(1)

def flow_exporter():
    while True:
        time.sleep(FLOW_TIMEOUT)
        try:
            current_flows = list(flow_data.keys())
        except RuntimeError:
            continue
        now = time.time()
        for flow_key in current_flows:
            if flow_key not in flow_data:
                continue
            flow = flow_data[flow_key]
            if now - flow['last_time'] > FLOW_TIMEOUT:
                remote_ip = flow_key[0]
                dst_port = flow_key[2] 
                flow_duration = (flow['last_time'] - flow['start_time']) * 1_000_000
                if flow_duration == 0: flow_duration = 1
                fwd_pkts = flow['fwd_pkts']
                bwd_pkts = flow['bwd_pkts']
                fwd_len = flow['fwd_len']
                bwd_len = flow['bwd_len']
                if len(flow['iat_list']) > 0:
                    iat_mean = np.mean(flow['iat_list']) * 1_000_000
                else:
                    iat_mean = 0
                syn_count = flow['syn_count']
                psh_count = flow['psh_count']
                ack_count = flow['ack_count']
                attacker_ip = remote_ip
                feature_string = (
                    f"{attacker_ip},"
                    f"{dst_port},{flow_duration},{fwd_pkts},{bwd_pkts},"
                    f"{fwd_len},{bwd_len},{iat_mean},{syn_count},"
                    f"{psh_count},{ack_count}\n"
                )
                with serial_lock:
                    try:
                        pico_serial.write(feature_string.encode('utf-8'))
                        response = pico_serial.readline().decode('utf-8').strip()
                        print(f"Flow: {attacker_ip}:{flow_key[1]} -> {HOST_IP}:{dst_port} | Pico says: {response}")
                    except serial.SerialException as e:
                        print(f"Serial write/read error: {e}")
                    except Exception as e:
                        print(f"Error processing flow: {e}")
                try:
                    del flow_data[flow_key]
                except KeyError:
                    pass

def packet_processor(packet):
    try:
        now = time.time()
        ip_layer = packet.getlayer(scapy.IP)
        if packet.haslayer(scapy.TCP):
            proto = "TCP"
            trans_layer = packet.getlayer(scapy.TCP)
            flags = trans_layer.flags
        else:
            proto = "UDP"
            trans_layer = packet.getlayer(scapy.UDP)
            flags = ""
        packet_len = ip_layer.len
        if ip_layer.src == HOST_IP:
            direction = 'bwd'
            remote_ip = ip_layer.dst
            remote_port = trans_layer.dport
            local_port = trans_layer.sport
        elif ip_layer.dst == HOST_IP:
            direction = 'fwd'
            remote_ip = ip_layer.src
            remote_port = trans_layer.sport
            local_port = trans_layer.dport
        else:
            return 
        flow_key = (remote_ip, remote_port, local_port, proto)
        if flow_key not in flow_data:
            flow_data[flow_key] = {
                'start_time': now,
                'last_time': now,
                'fwd_pkts': 0,
                'bwd_pkts': 0,
                'fwd_len': 0,
                'bwd_len': 0,
                'iat_list': [],
                'syn_count': 0, 
                'psh_count': 0,
                'ack_count': 0,
            }
        flow = flow_data[flow_key]
        if direction == 'fwd':
            flow['fwd_pkts'] += 1
            flow['fwd_len'] += packet_len
        else:
            flow['bwd_pkts'] += 1
            flow['bwd_len'] += packet_len
        if flow['fwd_pkts'] + flow['bwd_pkts'] > 1:
            flow['iat_list'].append(now - flow['last_time'])
        flow['last_time'] = now
        if 'S' in flags: flow['syn_count'] += 1
        if 'P' in flags: flow['psh_count'] += 1
        if 'A' in flags: flow['ack_count'] += 1
    except Exception as e:
        print(f"Packet processing error: {e}")

def main():
    if HOST_IP == "127.0.0.1":
        print("CRITICAL: Could not find a valid IP. Exiting.")
        print(f"Please check your '{NETWORK_INTERFACE}' interface name.")
        return
    print(f"Starting packet sniffer on {NETWORK_INTERFACE} for IP {HOST_IP}...")
    exporter = threading.Thread(target=flow_exporter, daemon=True)
    exporter.start()
    try:
        scapy.sniff(
            iface=NETWORK_INTERFACE, 
            prn=packet_processor, 
            store=0, 
            filter="ip and (tcp or udp)"
        )
    except Exception as e:
        print(f"Error starting sniffer: {e}")
        print("Do you need to run this script with sudo?")

if __name__ == "__main__":
    main()
