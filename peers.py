#!/usr/bin/python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from charms.reactive import RelationBase
from charms.reactive import hook
from charms.reactive import scopes


class OpenstackHAPeers(RelationBase):
    scope = scopes.UNIT

    @hook('{peers:openstack-ha}-relation-joined')
    def joined(self):
        conv = self.conversation()
        conv.set_state('{relation_name}.connected')

    @hook('{peers:openstack-ha}-relation-changed')
    def changed(self):
        conv = self.conversation()
        conv.set_state('{relation_name}.connected')
        if self.data_complete(conv):
            conv.set_state('{relation_name}.available')

    def ip_map(self, address_key='private-address'):
        nodes = []
        for conv in self.conversations():
            host_name = conv.scope.replace('/', '-')
            nodes.append((host_name, conv.get_remote(address_key)))

        return nodes

    @hook('{peers:openstack-ha}-relation-{broken,departed}')
    def departed_or_broken(self):
        conv = self.conversation()
        conv.remove_state('{relation_name}.connected')
        if not self.data_complete(conv):
            conv.remove_state('{relation_name}.available')

    def data_complete(self, conv):
        """
        Get the connection string, if available, or None.
        """
        data = {
            'private_address': conv.get_remote('private-address'),
        }
        if all(data.values()):
            return True
        return False

    def set_address(self, address_type, address):
        '''Advertise the address of this unit of a particular type

        :param address_type: str Type of address being advertised, e.g.
                                  internal/public/admin etc
        :param address: str IP of this unit in 'address_type' network

        @returns None'''

        for conv in self.conversations():
            conv.set_remote(
                key='{}-address'.format(address_type),
                value=address)

    def send_all(self, settings, store_local=False):
        '''Advertise a setting to peer units

        :param settings: dict Settings to be advertised to peers
        :param store_local: boolean Whether to store setting in local db

        @returns None'''
        for conv in self.conversations():
            conv.set_remote(data=settings)
            if store_local:
                conv.set_local(data=settings)

    def retrieve_local(self, key):
        '''Inspect conversation and look for key in local db

        :param key: str Key to look for in localdb
        @returns list: List of values of key
        '''
        values = []
        for conv in self.conversations():
            value = conv.get_local(key)
            if value:
                values.append(value)
        return values

    def retrieve_remote(self, key):
        '''Inspect conversation and look for key being advertised by peer

        :param key: str Key to look for from peer

        @returns list: List of values of key
        '''
        values = []
        for conv in self.conversations():
            value = conv.get_remote(key)
            if value:
                values.append(value)
        return values
