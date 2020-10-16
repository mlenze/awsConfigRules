# Ensure EC2 Instances are not of a type in a list of outdated instances
# Description: The function checks deployed EC2 instances against a supplied list of outdated / previous generation instance types.  It is meant to be called
# from AWS Config, and lists instances of outdated generations as non-compliant resources, while current generations are compliance.  Compliancy
# is determined based on the values contained in the outdatedInstanceList parameter, that is a comma seperated list of previous gen instance types.
#
# Trigger Type: Change Triggered
# Scope of Changes: EC2:Instance
# Required Parameter: outdatedInstanceList
# Example Value: m1.small,m1.medium
# 
# https://aws.amazon.com/ec2/previous-generation/ contains a list of outdated instance types
#
# The basis for this script is a AWS Config example script here: https://github.com/awslabs/aws-config-rules/blob/a9cde380ca50cc6fcf86955fcb5c2cc2f4072eb9/python/ec2_desired_instance_type-triggered.py
# The example script looks for instances to be of a particular type supplied by an input argument.

import boto3
import json

def is_applicable(config_item, event):
    status = config_item['configurationItemStatus']
    event_left_scope = event['eventLeftScope']
    test = ((status in ['OK', 'ResourceDiscovered']) and
            event_left_scope == False)
    return test


def evaluate_compliance(config_item, rule_parameters):
    if (config_item['resourceType'] != 'AWS::EC2::Instance'):
        return 'NOT_APPLICABLE'

    elif (config_item['configuration']['instanceType'] not in
            rule_parameters['outdatedInstanceList']):
        return 'COMPLIANT'
    else:
        return 'NON_COMPLIANT'


def lambda_handler(event, context):
    invoking_event = json.loads(event['invokingEvent'])
    rule_parameters = json.loads(event['ruleParameters'])

    compliance_value = 'NOT_APPLICABLE'

    if is_applicable(invoking_event['configurationItem'], event):
        compliance_value = evaluate_compliance(
                invoking_event['configurationItem'], rule_parameters)

    config = boto3.client('config')
    response = config.put_evaluations(
       Evaluations=[
           {
               'ComplianceResourceType': invoking_event['configurationItem']['resourceType'],
               'ComplianceResourceId': invoking_event['configurationItem']['resourceId'],
               'ComplianceType': compliance_value,
               'OrderingTimestamp': invoking_event['configurationItem']['configurationItemCaptureTime']
           },
       ],
       ResultToken=event['resultToken'])
