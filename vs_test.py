#!/usr/bin/env python

# This is a basic test of SoftLayer API:
# 1. create one instance with SSH key assigned,
# 2. wait for instance to get ready,
# 3. print instance info (login password, ip address)
# 4. destroy instance.

import SoftLayer
import traceback
import pprint

# read credentials from ~/.softlayer file
client = SoftLayer.Client()

# alternatively, pass credentials directly:
# client = SoftLayer.Client(
#     username='<USERNAME>',
#     api_key='<API KEY>')

vs_manager = SoftLayer.managers.vs.VSManager(client)

def list_instances_in_domain(domain):
    vs_list = vs_manager.list_instances(domain=domain)
    for vs in vs_list:
        print('{}\t{}'.format(vs['id'], vs['fullyQualifiedDomainName']))

def list_instances_with_tags(tags):
    if type(tags) is not list:
        raise Exception('`tags` must be a list! otherwise results are incorrect without warnings')

    print(tags)
    
    vs_list = vs_manager.list_instances(tags=tags)
    print('Found {} virtual servers with tags "{}"'.format(len(vs_list), ','.join(tags)))
    for vs in vs_list:
        # surprisingly `vs` object does not contain `tags` parameter
        # tag can be double checked by `get_tags` function
        pprint.pprint(vs)


def get_sshkey_id(label):
    key_manager = SoftLayer.managers.SshKeyManager(client)
    keys = key_manager.list_keys(label)
    if len(keys) != 1:
        raise Exception('Non-unique SSH key found for label=', label)
    id = keys[0]['id']
    return id

def create_instance():
    sshkey_id = get_sshkey_id('<SSH KEY LABEL>')

    print('Sending create_instance request...')
    vs = vs_manager.create_instance(
        hourly=True,
        datacenter='ams01',
        cpus=1,
        memory=1024,
        os_code='UBUNTU_14_64',
        domain='irina.com',
        hostname='vs-test',
        ssh_keys=[sshkey_id]
    )
    vs_id = vs['id']

    print('Instance id = ', vs_id)

    # wait for instance to get ready, wait for maximum 600 seconds
    # sometimes wait_for_ready fails with various SL exceptions,
    # so it is better to wrap the call to try-catch block.
    print('Waiting for instance to get ready...')
    try:
        vs_manager.wait_for_ready(instance_id=vs_id, limit=600)
    except Exception:
        print('Unexpected problem while waiting for instance ', vs_id)
        tb = traceback.format_exc()
        print(tb)

        print('Instance is still cooking, but I got to run...')
        return vs_id

    print('Instance is ready!')

    # get full information about instance just provisioned
    vs = vs_manager.get_instance(instance_id=vs_id)
    print(vs)
    print('Instance IP address: ', vs['primaryIpAddress'])
    print('Instance login data: ', vs['operatingSystem']['passwords'])

    return vs_id

def get_instance_info(instance_id):
    vs = vs_manager.get_instance(instance_id=instance_id)
    print(vs['primaryIpAddress'])
    print(vs['operatingSystem']['passwords'])

def cancel_instance(instance_id):
    print('Sending cancel request for instance id {}...'.format(instance_id))
    vs_manager.cancel_instance(instance_id)
    print('...cancel request sent')
    # TODO wait for instance to be really deleted - ?

def set_tags(instance_id, tags=None):
    # `tags` is list of tags
    # SL Python API Client does not support tags yet, so have to use API directly

    if type(tags) is not list:
        raise Exception('`tags` parameter must be a list')

    # SL API expects `tags` to be a comma separated list
    tags = ','.join(tags)

    vg = client['Virtual_Guest']
    vg.setTags(tags, id=instance_id)

def get_tags(instance_id):
    vg = client['Virtual_Guest']
    tags = vg.getTagReferences(id=instance_id)
    pprint.pprint(tags)

def main():

    test_create = False
    test_tags = True

    if (test_create):
        list_instances_in_domain('irina.com')
        vs_id = create_instance()
        list_instances_in_domain('irina.com')
        cancel_instance(vs_id)
        list_instances_in_domain('irina.com')

    if (test_tags):
        vs_id = 5473634
        get_instance_info(vs_id)
        tags = ['testtag1', 'testtag2']
        print('\n\nSetting tags `{}` on instance id={}'.format(','.join(tags), vs_id))
        set_tags(vs_id, tags)
        print('\n\nTags are set! Let\'s check tags on this instance:')
        get_tags(vs_id)
        print('\n\nNow check search instances by tags:')
        list_instances_with_tags(tags)
        print('\n\nFinally, try to search by one of tags:')
        list_instances_with_tags([tags[0]])

if __name__ == "__main__":
    main()
