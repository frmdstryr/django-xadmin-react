# coding=utf-8
"""
Copyright (c) 2017, Jairus Martin.
Distributed under the terms of the MIT License.
The full license is in the file COPYING.txt, distributed with this software.
Created on May 20, 2017
@author: jrm
"""
import json
import uuid
from channels.generic.websockets import JsonWebsocketConsumer
from xadmin.plugins.ajax import *
from datetime import datetime
from django.apps import apps


class ReactEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


class ReactWebsocket(JsonWebsocketConsumer):
    http_user = True

    # Set to True if you want it, else leave it out
    strict_ordering = False

    def connection_groups(self, **kwargs):
        """
        Called to return the list of groups to automatically add/remove
        this connection to/from.
        """
        return ["react"]

    def connect(self, message, **kwargs):
        """
        Perform things on connection start
        """
        super(ReactWebsocket, self).connect(message, **kwargs)
        #: Add
        react = React.get(self.message.user)
        react.websockets.append(self)

    def receive(self, content, **kwargs):
        """
        Called when a message is received with decoded JSON content
        """
        react = React.get(self.message.user)
        if not react.view:
            #: Get it from te message
            react.load_view(content.get('path'))
        if not react.view:
            #: So.. i can't print apparently
            #print("View is missing abort! React: {} {}".format(react, content))
            return

        #: May not yet exist
        resp = react.view.websocket_response(self, self.message, content)

        #: Push to everyone logged in as this user
        for ws in react.websockets:
            ws.send(resp)

    def encode_json(cls, content):
        return json.dumps(content, cls=ReactEncoder)

    def disconnect(self, message, **kwargs):
        """
        Perform things on connection close
        """
        #: Remove
        react = React.get(self.message.user)
        try:
            react.websockets.remove(self)
        except ValueError:
            pass


class React(object):
    """ This caches based on the current user
    """

    #: TODO: Should use django cache..
    __cache__ = {}
    __registry__ = {}

    @staticmethod
    def get(user):
        if user not in React.__cache__:
            return React(user)
        return React.__cache__[user]

    def __init__(self, user):
        React.__cache__[user] = self
        self.admin_site = site
        self.user = user
        self.model = None
        self.view = None
        self.path = None
        self.websockets = []

    def load_view(self, path):
        """
        Path is the window location: ex app/model/
        Sets the model and view if none exists
        
        :param path: 
        :return: 
        """
        #: Get the model
        model = apps.get_model(path.split("/")[0:2])
        self.model = model
        self.view = site._registry[model]


class ReactPlugin(BaseAdminPlugin):
    react_template = 'react/react_list.html'
    list_react = []

    def init_request(self, *args, **kwargs):
        #: Add _react=0 flag to disable
        try:
            enable_flag = int(self.request.GET.get('_react', 1))
        except:
            enable_flag = True

        active = bool(self.request.method == 'GET' and self.list_react
                      and bool(enable_flag))

        self.admin_view.react_active = active
        if active:
            self.admin_view.object_list_template = self.admin_view.get_template_list(self.react_template)
            #: Save the plugin
            user = self.request.user

            #: This is so flipping ugly
            react = React.get(user)
            react.view = self
            react.model = self.model
            react.path = self.request.path
            react.user = self.request.user

        return active

    def result_item(self, item, obj, field_name, row):
        """ Add object to the item"""
        item.obj = obj
        return item

    def websocket_response(self, websocket, message=None, content=None):
        mid = str(uuid.uuid4().bytes)
        #print("[{}] Request: {} {} {}".format(mid,websocket, message, content))
        av = self.admin_view

        #: If the admin view want's to handle it
        if hasattr(av, 'websocket_response'):
            r = av.websocket_response(websocket, message, content)
            if r:
                #print("[{}] Response: {}".format(mid, r))
                return r

        #: Refresh it
        av.make_result_list()

        #: else do the default
        #: Skip checkbox, not sure why there's two
        base_fields = [f for f in av.get_list_display() if f!='action_checkbox']

        headers = [force_text(c.text) for c in av.result_headers(
        ).cells if c.field_name in base_fields]

        objects = [[self.encode_result_item(o)
                     for i, o in enumerate(filter(lambda c:c.field_name in base_fields, r.cells))]
                   for r in av.results()]
        r = {'headers': headers, 'objects': objects,
             'total_count': av.result_count, 'has_more': av.has_more,
             'error': None,
             'status': 'OK'}
        #print("[{}] Response: {}".format(mid, r))
        return r

    def encode_result_item(self, item):
        """ Encode for handling with react """

        if item.field and item.field.flatchoices:
            result = escape(str(dict(item.field.flatchoices).get(item.value,item.value)))
        elif isinstance(item.value, (bool, tuple, list, dict)):
            #: If it can be encoded, ship it as is
            try:
                json.dumps(item.value, cls=ReactEncoder)
                result = item.value
            except TypeError:
                result = escape(str(item.value))
        else:
            result = escape(str(item.value))
        #: TODO: Choices!

        #: Edit buttons
        if item.field and item.field.editable and (item.field_name in self.admin_view.list_editable):
            #: Assume it means editable...
            #: Hack.. Pull url from btn..
            pk = getattr(item.obj, item.obj._meta.pk.attname)
            url = self.admin_view.model_admin_url('patch', pk) + '?fields=' + item.field_name
            result = {
                'type': 'editable',
                'field': item.field_name,
                'url': url,
                'value': result,
            }
        return result

    @classmethod
    def notify(cls, model):
        """ Notify clients that this model changed """
        #: TODO: Should us signals but this works for now...
        for react in React.__cache__.values():
            if react.model != model:
                continue

            #: Notify on save
            for ws in react.websockets:
                ws.send(react.view.websocket_response(ws))

site.register_plugin(ReactPlugin, ListAdminView)
