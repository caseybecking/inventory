from django.test import TestCase

from mozdns.domain.models import Domain
from mozdns.ptr.models import PTR
from mozdns.address_record.models import AddressRecord

from systems.models import System

from core.interface.static_intr.models import StaticInterface
from core.range.utils import start_end_filter, range_usage
from core.utils import two_to_one
import ipaddr


class UsageTests(TestCase):
    def setUp(self):
        Domain.objects.get_or_create(name="com")
        self.domain, _ = Domain.objects.get_or_create(name="foo.com")
        Domain.objects.get_or_create(name="arpa")
        Domain.objects.get_or_create(name="in-addr.arpa")
        Domain.objects.get_or_create(name="10.in-addr.arpa")

    def test0(self):
        ip_start = "10.0.0.0"
        ip_end = "10.0.0.9"
        ptr = PTR(name="foo.mz", ip_str="10.0.0.5", ip_type='4')
        ptr.full_clean()
        ptr.save()
        istart, iend, ipf_q = start_end_filter(ip_start, ip_end, '4')
        addrs = list(AddressRecord.objects.filter(ipf_q).
                     order_by('ip_lower').order_by('ip_upper'))
        ptrs = list(PTR.objects.filter(ipf_q).
                    order_by('ip_lower').order_by('ip_upper'))
        intrs = list(StaticInterface.objects.filter(ipf_q).
                     order_by('ip_lower').order_by('ip_upper'))
        self.assertFalse(addrs)
        self.assertEqual(ptr.pk, ptrs[0].pk)
        self.assertFalse(intrs)

        range_details = range_usage(ip_start, ip_end, '4')
        self.assertEqual(9, range_details['unused'])
        self.assertEqual(1, range_details['used'])
        self.assertEqual([(int(istart) + 0, int(istart) + 4),
                          (int(istart) + 6, int(istart) + 9)],
                         range_details['free_ranges'])

    def test1(self):
        ip_start = "10.0.0.10"
        ip_end = "10.0.0.19"

        ptr = PTR(name="foo.mz", ip_str="10.0.0.15", ip_type='4')
        ptr.full_clean()
        ptr.save()

        a = AddressRecord(
            label="foo", domain=self.domain, ip_str="10.0.0.16", ip_type='4')
        a.full_clean()
        a.save()

        istart, iend, ipf_q = start_end_filter(ip_start, ip_end, '4')
        addrs = list(AddressRecord.objects.filter(ipf_q).
                     order_by('ip_lower').order_by('ip_upper'))
        ptrs = list(PTR.objects.filter(ipf_q).
                    order_by('ip_lower').order_by('ip_upper'))
        intrs = list(StaticInterface.objects.filter(ipf_q).
                     order_by('ip_lower').order_by('ip_upper'))
        self.assertEqual(a.pk, addrs[0].pk)
        self.assertEqual(ptr.pk, ptrs[0].pk)
        self.assertFalse(intrs)

        range_details = range_usage(ip_start, ip_end, '4')
        self.assertEqual(8, range_details['unused'])
        self.assertEqual(2, range_details['used'])
        self.assertEqual([(int(istart), int(istart) + 4),
                          (int(istart) + 7, int(istart) + 9)],
                         range_details['free_ranges'])

    def test2(self):
        ip_start = "10.0.1.0"
        ip_end = "10.0.1.99"
        ptr = PTR(name="foo.mz", ip_str="10.0.1.3", ip_type='4')
        ptr.full_clean()
        ptr.save()

        a = AddressRecord(label="foo", domain=self.domain, ip_str="10.0.1.3",
                          ip_type='4')
        a.full_clean()
        a.save()

        s = System(hostname="foo.mozilla.com")
        s.save()
        intr = StaticInterface(
            label="foo", domain=self.domain, ip_str="10.0.1.4",
            ip_type='4', system=s, mac="00:11:22:33:44:55")
        intr.full_clean()
        intr.save()

        istart, iend, ipf_q = start_end_filter(ip_start, ip_end, '4')
        addrs = list(AddressRecord.objects.filter(ipf_q).
                     order_by('ip_lower').order_by('ip_upper'))
        ptrs = list(PTR.objects.filter(ipf_q).
                    order_by('ip_lower').order_by('ip_upper'))
        intrs = list(StaticInterface.objects.filter(ipf_q).
                     order_by('ip_lower').order_by('ip_upper'))
        self.assertEqual(a.pk, addrs[0].pk)
        self.assertEqual(ptr.pk, ptrs[0].pk)
        self.assertEqual(intr.pk, intrs[0].pk)

        range_details = range_usage(ip_start, ip_end, '4')
        self.assertEqual(98, range_details['unused'])
        self.assertEqual(2, range_details['used'])
        self.assertEqual([(int(istart) + 0, int(istart) + 2),
                          (int(istart) + 5, int(istart) + 99)],
                         range_details['free_ranges'])

    def test3(self):
        # https://github.com/mozilla/inventory/issues/19
        def ip_to_str(u, l):
            return ipaddr.IPv6Address(two_to_one(u, l))
        # A
        a_i_upper = 2
        a_i_lower = 2
        a_ip = ip_to_str(a_i_upper, a_i_lower)

        # start
        filter_start_i_upper = 1
        filter_start_i_lower = 3
        start_ip = ip_to_str(filter_start_i_upper, filter_start_i_lower)

        # end
        filter_end_i_upper = 3
        filter_end_i_lower = 0
        end_ip = ip_to_str(filter_end_i_upper, filter_end_i_lower)

        """
        (3,3) (3,2) (3,1) (3,0) (2,3) (2,2) (2,1) (2,0) (1,3) (1,2) (1,1) (1,0)
                           end         A                start
        """

        a = AddressRecord.objects.create(
            label="foo3", domain=self.domain, ip_str=a_ip,
            ip_type='6'
        )

        istart, iend, ipf_q = start_end_filter(start_ip, end_ip, '6')
        self.assertEqual(a.pk, AddressRecord.objects.get(ipf_q).pk)
