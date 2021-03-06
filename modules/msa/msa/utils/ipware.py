"""This module is directly ported from django-ipware"""

# Copyright © Val Neekman (Neekware Inc.) [ info@neekware.com, @vneekman ]
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 
# 3. Neither the name of this project nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import socket


# Search for the real IP address in the following order
IPWARE_META_PRECEDENCE_ORDER = (
    'HTTP_X_FORWARDED_FOR',  # (client, proxy1, proxy2) OR (proxy2, proxy1, client)
    'HTTP_CLIENT_IP',
    'HTTP_X_REAL_IP',
    'HTTP_X_FORWARDED',
    'HTTP_X_CLUSTER_CLIENT_IP',
    'HTTP_FORWARDED_FOR',
    'HTTP_FORWARDED',
    'HTTP_VIA',
    'REMOTE_ADDR',
)

# Private IP addresses
# http://en.wikipedia.org/wiki/List_of_assigned_/8_IPv4_address_blocks
# http://www.ietf.org/rfc/rfc3330.txt (IPv4)
# http://www.ietf.org/rfc/rfc5156.txt (IPv6)
IPWARE_PRIVATE_IP_PREFIX = (
    '0.',  # externally non-routable
    '10.',  # class A private block
    '169.254.',  # link-local block
    '172.16.', '172.17.', '172.18.', '172.19.',
    '172.20.', '172.21.', '172.22.', '172.23.',
    '172.24.', '172.25.', '172.26.', '172.27.',
    '172.28.', '172.29.', '172.30.', '172.31.',  # class B private blocks
    '192.0.2.',  # reserved for documentation and example code
    '192.168.',  # class C private block
    '255.255.255.',  # IPv4 broadcast address
) + (
    '2001:db8:',  # reserved for documentation and example code
    'fc00:',  # IPv6 private block
    'fe80:',  # link-local unicast
    'ff00:',  # IPv6 multicast
)

IPWARE_LOOPBACK_PREFIX = (
    '127.',  # IPv4 loopback device
    '::1',  # IPv6 loopback device
)

IPWARE_NON_PUBLIC_IP_PREFIX = IPWARE_PRIVATE_IP_PREFIX + IPWARE_LOOPBACK_PREFIX


def is_valid_ipv4(ip_str):
    """
    Check the validity of an IPv4 address
    """
    try:
        socket.inet_pton(socket.AF_INET, ip_str)
    except AttributeError:
        try:  # Fall-back on legacy API or False
            socket.inet_aton(ip_str)
        except (AttributeError, socket.error):
            return False
        return ip_str.count('.') == 3
    except socket.error:
        return False
    return True


def is_valid_ipv6(ip_str):
    """
    Check the validity of an IPv6 address
    """
    try:
        socket.inet_pton(socket.AF_INET6, ip_str)
    except socket.error:
        return False
    return True


def is_valid_ip(ip_str):
    """
    Check the validity of an IP address
    """
    return is_valid_ipv4(ip_str) or is_valid_ipv6(ip_str)


def get_ip(request, real_ip_only=False, right_most_proxy=False):
    """
    Returns client's best-matched ip-address, or None
    """
    best_matched_ip = None
    for key in IPWARE_META_PRECEDENCE_ORDER:
        value = request.META.get(key, '').strip()
        if value != '':
            ips = [ip.strip().lower() for ip in value.split(',')]
            if right_most_proxy:
                ips = reversed(ips)
            for ip_str in ips:
                if ip_str and is_valid_ip(ip_str):
                    if not ip_str.startswith(IPWARE_NON_PUBLIC_IP_PREFIX):
                        return ip_str
                    if not real_ip_only:
                        loopback = IPWARE_LOOPBACK_PREFIX
                        if best_matched_ip is None:
                            best_matched_ip = ip_str
                        elif best_matched_ip.startswith(loopback) and not ip_str.startswith(loopback):
                            best_matched_ip = ip_str
    return best_matched_ip


def get_real_ip(request, right_most_proxy=False):
    """
    Returns client's best-matched `real` ip-address, or None
    """
    return get_ip(request, real_ip_only=True, right_most_proxy=right_most_proxy)
