#!/usr/bin/eval python

"""
Driver program to test pu.py
"""

# import pu
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(__file__)
print(sys.path)
import pu.array
from pu.array import array

print(dir(pu.array))

if __name__ == "__main__":
    host = '192.168.23.21'
    user = 'configureme'
    password = 'Password123#'

    # disable_urllib_warnings()

    logging.basicConfig(level=logging.DEBUG)
    logging.debug('host: {} - user: {} - password: {}'.format(host, user, password))
    a = array(ipaddr=host, user=user, password=password)
    print(a)
