import ipaddress


def anonymize_ip(ip):
    """
    The network part of ip: an IPv4 address without its last octet, an IPv6
    address without its last 80 bits (a /48 spans many customers, as a /24 does).
    """
    if not ip:
        return ip
    address = ipaddress.ip_address(ip)
    if address.version == 6 and address.ipv4_mapped:
        address = address.ipv4_mapped
    prefix = 24 if address.version == 4 else 48
    return str(ipaddress.ip_network(f"{address}/{prefix}", strict=False).network_address)
