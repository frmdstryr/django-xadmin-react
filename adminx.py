"""
Copyright (c) 2017, Jairus Martin.
Distributed under the terms of the MIT License.
The full license is in the file COPYING.txt, distributed with this software.
Created on Oct 31, 2017
@author: jrm
"""
import xadmin
from .plugins import react #: Make sure django-xadmin loads the plugin
from .models import User

class UserAdmin(object):
    model_icon = 'fa fa-users'
    list_react = True #: Enable the plugin
    list_display = ('id', 'name', '_updated', '_created')

    def _updated(self, obj):
        return {'type': 'fromNow', 'value': obj.updated}

    def _created(self, obj):
        return {'type': 'date', 'value': obj.created}

    def websocket_response(self, websocket, message=None, content=None):
        """ We can override the default response or do some processing and let
            the plugin return the default
        """
        msg = content.get('message', "") if content else ""
        if msg.startswith("#do-somthing-"):
            uid = msg.split("-")[-1]
            try:
                u = User.objects.get(id=uid)
                #: Handle this message
                u.save()
            except Exception as e:
                return {'error': e, 'status': 'INVALID_ID'}
            #: otherwise return default (OK) response!


xadmin.site.register(User, UserAdmin)
