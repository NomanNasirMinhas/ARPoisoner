import asyncio
import logging
import subprocess
import re

logging.basicConfig(level=logging.INFO)

def get_ip_range():
    # Use `ip a` command to get the network interface and IP address
    output = subprocess.run(['ip', 'a'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    # Extract the IP address and prefix from the interface
    ip_pattern = re.compile(r'inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/(\d{1,2})')
    match = ip_pattern.search(output)
    if match:
        # Calculate the start and end IP addresses in the subnet
        ip_prefix = match.group(1)
        prefix = int(match.group(2))
        num_ips = 2 ** (32 - prefix)
        start_ip = int(ip_prefix.split('.')[-1])
        end_ip = (start_ip + num_ips - 1) % 256
        return f"{ip_prefix[:-1]}{start_ip}-{ip_prefix[:-1]}{end_ip}"
    else:
        raise Exception("Failed to find IP address and prefix")

async def send_arp_request(ip_address):
    # Use `arping` command to send an ARP request to the specified IP address
    proc = await asyncio.create_subprocess_exec(
        'arping', '-c', '1', '-w', '1', ip_address,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    if proc.returncode == 0:
        logging.info(f"Sent ARP request to {ip_address}")
    else:
        logging.warning(f"Failed to send ARP request to {ip_address}: {stderr.decode('utf-8')}")

async def main():
    ip_range = get_ip_range()
    logging.info(f"Sending ARP requests to IP range: {ip_range}")
    # Create a task for each IP address in the range
    tasks = [send_arp_request(ip_address) for ip_address in ip_range]
    # Wait for all tasks to complete
    await asyncio.wait(tasks)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
