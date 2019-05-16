# This script comes with no warranty use at your own risk
#
# Title: rubrik-ec2-snap-replicate
# Author: Damani Norman - Rubrik Ranger Team
# Date: 05/15/2019
#
# Description:
#
# Check the status of the copied AMI and return the result alongside the original event

import logging
import boto3

def lambda_handler(event, context):

    # init logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
 
    ec2resource = boto3.resource('ec2', event['destination_region'])
    destination_ami = ec2resource.Image(event['destination_ami_id'])

    if event['debug']:
        logger.info('destination_ami.state is: {}'.format(destination_ami.state))
    
    # return status in modified event
    if destination_ami.state == 'available':
        event['rkstatus'] = 'dest_available'
        logger.info('Tag operation can proceed for snapshots of AMI {}.'.format(event['destination_ami_id']))
        return event
    elif destination_ami.state == 'pending':
        event['rkstatus'] = 'dest_pending'
        logger.info('{} is pending, sleeping.'.format(event['destination_ami_id']))
        return event
    else:
        event['rkstatus'] = 'failed'
        logger.info('{} is failed, quitting'.format(event['destination_ami_id']))
        return event