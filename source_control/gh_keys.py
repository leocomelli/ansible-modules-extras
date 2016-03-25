#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, André Paramés <git@andreparames.com>
# Based on the Git module by Leonardo Comelli <leonardo.comelli@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: gh_keys
version_added: "2.1" 
short_description: Manages GitHub ssh keys.
description:
  - The module manages the ssh key for a specific user through Github API v3.

options:
  state:
    description: 
      - This tells the gh_keys module what you want it to do.
    choices: [ present, absent ]
    default: present

  user:
    description: 
      - Github username.
    required: true

  password:
    description: 
      - Github password. If 2FA is enabled for your account, you should generate a new personal access token.
    required: true
    default: none

  title:
    description: 
      - Title of the new ssh key. Required for the present state
    required: false
    default: none

  key:
    description: 
      - The path of file that contains the public key. Required for the present state
    required: false
    default: none

  key_id:
    description: 
      - The key id provided by Github. Required for the absent state
    required: false
    default: none

author: Leonardo Comelli (@leocomelli)
'''

EXAMPLES = '''
# Example from Ansible Playbooks

# Adds a new public key
- gh_keys: state=present user=leocomelli password=secret title=my_new_key key=/home/leocomelli/.ssh/id_rsa.pub

# Removes an existing ssh key
- gh_keys: state=absent user=leocomelli password=secret key_id=8767854
'''

RETURN = '''
output:
  description: the data returned by Github according to the state
  returned: success
  type: dict
  sample: 
    {
        "created_at": "2016-03-25T17:08:51Z", 
        "id": 12345678, 
        "key": "ssh-rsa AAAA...", 
        "read_only": false, 
        "title": "devel", 
        "url": "https://api.github.com/user/keys/12345678", 
        "verified": true
    }
'''

import base64
try:
  import json
except ImportError:
  import simplejson as json

GH_API_URL = "https://api.github.com/%s"

class GHKeys(object):

  def __init__(self, module):
    self.module = module
    self.state = module.params['state']
    self.user   = module.params['user']
    self.password = module.params['password']
    self.title  = module.params['title']
    self.key    = module.params['key']
    self.key_id = module.params['key_id']
  
  def handle_state(self):
    return {
      'present' : self.add_key,
      'absent'  : self.remove_key
    }[self.state]()

  def add_key(self):
    f = open(self.key, 'r')
    try:
      content = f.readline()
    finally:
      f.close()
    
    url = GH_API_URL %  "user/keys"
    headers = self.get_auth_header(self.user, self.password)
    data = json.dumps({ 'title' : self.title, 'key' : content })
    response, info = fetch_url(self.module, url, headers=headers, data=data, method='POST')
      
    return self.handle_response(response, info)

  def remove_key(self):
    url = GH_API_URL %  "user/keys/%s" % self.key_id
    headers = self.get_auth_header(self.user, self.password)
    response, info = fetch_url(self.module, url, headers=headers, method='DELETE')

    return self.handle_response(response, info)

  def get_auth_header(self, user, password):
    auth = base64.encodestring('%s:%s' % (user, password)).replace('\n', '')
    headers = {
      'Authorization': 'Basic %s' % auth,
    }
    return headers

  def handle_response(self, response, info):
    if info['status'] == 200:
      return response.read()
    else:
      msg = info['msg']
      if info['status'] == 422:
        msg += " - key is already in use"
      raise RuntimeError(msg)

def check_required_fields(module):
  present_fields = ['title', 'key', 'password']
  absent_fields = ['key_id', 'password']

  if module.params['state'] == 'present':
    fields = present_fields
  else:
    fields = absent_fields

  for field in fields:
    if module.params[field] is None:
      raise ValueError(field + " cannot be null for state [" + module.params['state'] + "]")

def main():
  module = AnsibleModule(
    argument_spec = dict(
      password = dict(no_log=True),
      title    = dict(),
      key      = dict(),
      key_id   = dict(),
      user     = dict(required=True),
      state    = dict(choices=['present', 'absent'], default='present'),
    ),
    supports_check_mode=True
  )  

  check_required_fields(module)
  if module.check_mode:
    module.exit_json(changed=True)

  gh_keys = GHKeys(module)

  try:
    response = gh_keys.handle_state()
    module.exit_json(changed=True, result=response)
  except (RuntimeError, ValueError), err:
    module.fail_json(msg=err.args)

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
  main()
