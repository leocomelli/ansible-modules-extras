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
module: gh_keys_facts
version_added: "2.1" 
short_description: GitHub ssh keys facts.
description:
  - GitHub ssh keys facts.

options:
  user:
    description: 
      - Github username.
    required: true

  password:
    description: 
      - Github password. If 2FA is enabled for your account, you should generate a new personal access token. Required for get_key, add_key and remove_key 
    required: false
    default: none

  key_id:
    description: 
      - The key id provided by Github.
    required: false
    default: none    

author: Leonardo Comelli (@leocomelli)
'''

EXAMPLES = '''
# Example from Ansible Playbooks

# Gathering facts about all keys of a non-authenticated user (limit informations)
- gh_keys_facts: user=leocomelli

# Gathering facts about all keys of an authenticated user
- gh_keys_facts: user=leocomelli password=secret

# Gathering facts about a specific key of an authenticated user
- gh_keys_facts: user=leocomelli password=secret key_id=8767854
'''

RETURN = '''
output:
  description: the data returned by Github API
  returned: success
  type: dict
  sample: 
    {
        "created_at": "2016-03-22T14:49:01Z", 
        "id": 12345678, 
        "key": "ssh-rsa AAA...", 
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

def facts(module):
  user = module.params['user']
  password = module.params['password']
  key_id = module.params['key_id']

  if password is None:
    url = GH_API_URL % "users/%s/keys" % user
    response, info = fetch_url(module, url)      
  else:
    url = GH_API_URL % "user/keys"
    headers = headers = { 'Authorization': 'Basic %s' % base64.encodestring('%s:%s' % (user, password)).replace('\n', ''), }
    if key_id is not None:
      url = GH_API_URL %  "user/keys/%s" % key_id
    response, info = fetch_url(module, url, headers=headers)

  return response, info


def main():
  module = AnsibleModule(
    argument_spec = dict(
      user     = dict(required=True),
      password = dict(no_log=True),
      key_id   = dict(),
    )
  )  

  response, info = facts(module)

  if info['status'] == 200:
    module.exit_json(changed=True, result=response.read())
  else:
    module.fail_json(msg=info['msg'])

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
  main()
