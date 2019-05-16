# This script comes with no warranty use at your own risk
#
# Title: rubrik-ec2-snap-replicate
# Author: Bill Gurling - Rubrik Ranger Team
# Date: 05/15/2019
#
# Description:
#
# Tag Rubrik Replicated AMIs snapshots

import logging
import boto3
import json
import copy

# logging init
logger = logging.getLogger()
#logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    # start logging
    data = json.dumps(event)
    logger.info('Starting snapshot tag job based on this event:')
    logger.info(data)

    # grab parameters from our event
    resourceId = event['resourceId']
    source_region = event['source_region']
    destination_ami_id = event['destination_ami_id']
    debug = event['debug']
    destination_region = event['destination_region']

    # init boto3
    source_resource = boto3.resource('ec2', source_region)
    destination_resource = boto3.resource('ec2', destination_region)
    destination_client = boto3.client('ec2', destination_region)

    # source AMI
    source_ami = source_resource.Image(resourceId)

    # Grab destination AMI details
    destination_ami = destination_resource.Image(destination_ami_id)

    cur_tags = boto3_tag_list_to_ansible_dict(source_ami.tags)
    new_tags = copy.deepcopy(cur_tags)
    new_tags['rk_source_ami'] = source_ami.id
    new_tags['rk_source_region'] = source_region
      
    if debug:
        logger.info('destination_ami_id is {}'.format(destination_ami_id))
        logger.info('destination_ami is {}'.format(destination_ami))
        logger.info('destination_ami.block_device_mappings is {}'.format(destination_ami.block_device_mappings))

    tag_snapshot = {}
    for device in destination_ami.block_device_mappings:
        if 'SnapshotId' in device['Ebs']:
            snapshot = device['Ebs']['SnapshotId']
            tag_snapshot.update(destination_client.create_tags(Resources=[snapshot], Tags=ansible_dict_to_boto3_tag_list(new_tags)))

    return tag_snapshot

def boto3_tag_list_to_ansible_dict(tags_list):
    tags_dict = {}
    for tag in tags_list:
        if 'key' in tag and not tag['key'].startswith('aws:'):
            tags_dict[tag['key']] = tag['value']
        elif 'Key' in tag and not tag['Key'].startswith('aws:'):
            tags_dict[tag['Key']] = tag['Value']

    return tags_dict


def ansible_dict_to_boto3_tag_list(tags_dict):
    tags_list = []
    for k, v in tags_dict.items():
        tags_list.append({'Key': k, 'Value': v})

    return tags_list
