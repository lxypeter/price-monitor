# -*- coding: utf-8 -*-

'''
configuration
'''

from .default import DefaultConfig

CONFIG = DefaultConfig

try:
    from .instance import InstanceConfig
    CONFIG = InstanceConfig
except ImportError:
    pass
