# This script comes with no warranty use at your own risk
#
# Title: rubrik-ec2-snap-replicate
# Author: Bill Gurling - Rubrik Ranger Team
# Date: 10/19/2018
#
# Description:
#
# Check the status of rubrik created AMI and return the result alongside the original event

import logging
import boto3

def lambda_handler(event, context):

    # init logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    #Debug event details
    if event['debug'] is 'true':
        logger.debug('Event is {}'.format(event))

    
    # check resource type - quit if not an ami, check ami status if an ami
    if 'ami-' not in event['resource_id']:
        logger.info('Resource is not an AMI, quitting.')
        event['rkstatus'] = 'noami'
        return event
    else:
        logger.info('{} is an AMI, verifying state...'.format(event['resource_id']))
    
    ec2_resource = boto3.resource('ec2', event['source_region'])
    source_ami = ec2_resource.Image(event['resource_id'])
    
    # return status in modified event
    if source_ami.state == 'available':
        event['rkstatus'] = 'available'
        logger.info('{} is available, copy operation can proceed.'.format(event['resource_id']))
        return event
    elif source_ami.state == 'pending':
        event['rkstatus'] = 'pending'
        logger.info('{} is pending, sleeping.'.format(event['resource_id']))
        return event
    else:
        event['rkstatus'] = 'failed'
        logger.info('{} is failed, quitting'.format(event['resource_id']))
        return event