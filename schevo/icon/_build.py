"""Do a one-time build of default.png"""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.


if __name__ == '__main__':
    f = file('default.png', 'rb')
    default_png = f.read()
    f.close()
    f = file('_default_png.py', 'wU')
    f.write('DEFAULT_PNG = %r\n' % default_png)
    f.close()
