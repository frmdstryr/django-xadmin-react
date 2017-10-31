"""
Copyright (c) 2017, Jairus Martin.
Distributed under the terms of the MIT License.
The full license is in the file COPYING.txt, distributed with this software.
Created on Oct 31, 2017
@author: jrm
"""
from channels import route, route_class
from .plugins import react

channel_routing = [
    route_class(react.ReactWebsocket, path=r"^/live/"),
]
