# This script comes with no warranty use at your own risk
#
# Title: rubrik-ec2-snap-replicate
# Author: Bill Gurling - Rubrik Ranger Team
# Date: 10/19/2018
#
# Description:
#
# Delete Expired AMIs when Rubrik service account GCs them

import logging
import boto3
import json

# logging init
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    # start logging
    data = json.dumps(event)
    logger.info('Starting replica delete job based on this event:')
    logger.info(data)

    # grab parameters from our event
    resourceId = event['resourceId']
    source_region = event['source_region']
    logger.info('Source ami in {} is {}'.format(resourceId, source_region))

    # Configurable - Rubrik created EC2 snapshots will be deleted from this region.
    destination_region = event['destination_region']
    

    # init boto3
    destination_resource = boto3.resource('ec2', destination_region)
    destination_client = boto3.client('ec2', destination_region)

    # look up the image we need to deregister in our destination region
    response = destination_client.describe_images(Filters=[{'Name':'tag:rk_source_ami', 'Values':[resourceId]},{'Name':'tag:rk_source_region', 'Values':[source_region]}])

    # get the image object in destination region if the image exists
    try:
        logger.info('Attempting to find replica ami in {} corresponding to {} in {}'.format(destination_region, resourceId, source_region))
        destination_ami = destination_resource.Image(response['Images'][0]['ImageId'])
    except IndexError:
        logger.info('No replica corresponding to {} found, exiting.'.format(resourceId))
        return 'IndexError'

    logger.info('Found replica ami {} in {}'.format(destination_ami.image_id, destination_region))    

    # get list of snapshots we need to remove after deregistering the replica ami
    logger.info('Iterating snapshots associated with {}'.format(destination_ami.image_id))
    snap_purge = [blockdevice['Ebs']['SnapshotId'] for blockdevice in destination_ami.block_device_mappings]
    logger.info('Found the following snapshots associated with {}:'.format(destination_ami.image_id))
    logger.info(snap_purge)

    # deregister the image
    logger.info('Attempting to deregister {} in {}'.format(destination_ami.image_id, destination_region))
    destination_ami.deregister()

    # remove the ebs volumes
    for snapshotid in snap_purge:
        snapshot = destination_resource.Snapshot(snapshotid)
        logger.info('Attempting to delete {} in {}'.format(snapshotid, destination_region))
        snapshot.delete()

    return 'Complete'