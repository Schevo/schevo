"""
$URL: svn+ssh://svn/repos/trunk/durus/test/utest_utils.py $
$Id: utest_utils.py 27079 2005-07-25 20:54:05Z dbinger $
"""
from schevo.store.utils import format_oid, u64, p64, u32, p32


class Test(object):

    def test_check_format_oid(self):
        assert format_oid('A'*8) == '4702111234474983745'

    def test_check_p64_u64(self):
        for x in range(3):
            assert len(p64(x)) == 8
            assert u64(p64(x)) == x

    def test_check_p32_u32(self):
        for x in range(3):
            assert len(p32(x)) == 4
            assert x == u32(p32(x))
