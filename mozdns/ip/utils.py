import ipaddr
from django.core.exceptions import ValidationError
from mozdns.validation import validate_ip_type


def ip2dns_form(ip, ip_type='4', uppercase=False):
    """Convert an ip to dns zone form. The ip is assumed to be in valid dotted
    decimal format."""
    if not isinstance(ip, basestring):
        raise ValidationError("Ip is not of type string.")
    validate_ip_type(ip_type)
    octets = ip.split('.')
    if ip_type == '4':
        name = '.in-addr.arpa'
    if ip_type == '6':
        name = '.ipv6.arpa'
    if uppercase:
        name = name.uppercase

    name = '.'.join(list(reversed(octets))) + name
    return name


"""
>>> nibblize('2620:0105:F000::1')
'2.6.2.0.0.1.0.5.F.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.1'
>>> nibblize('2620:0105:F000:9::1')
'2.6.2.0.0.1.0.5.f.0.0.0.0.0.0.9.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.1'
>>> nibblize('2620:0105:F000:9:0:1::1')
'2.6.2.0.0.1.0.5.f.0.0.0.0.0.0.9.0.0.0.0.0.0.0.1.0.0.0.0.0.0.0.1'
"""


def nibbilize(addr):
    """Given an IPv6 address is 'colon' format, return the address in
    'nibble' form::

        nibblize('2620:0105:F000::1')
        '2.6.2.0.0.1.0.5.F.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.1'

    :param addr: The ip address to convert
    :type addr: str
    """
    try:
        ip_str = ipaddr.IPv6Address(str(addr)).exploded
    except ipaddr.AddressValueError:
        raise ValidationError("Error: Invalid IPv6 address {0}.".format(addr))

    return '.'.join(list(ip_str.replace(':', '')))