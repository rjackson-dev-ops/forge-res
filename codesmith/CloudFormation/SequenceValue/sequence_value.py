import logging

import boto3
from box import Box
from crhelper import CfnResource

from codesmith.common import naming, cfn
from codesmith.common.calc import calculator, SSM_PARAMETER_DESCRIPTION
from codesmith.common.cfn import resource_properties, logical_resource_id
from codesmith.common.schema import non_empty_string, tolerant_schema
from codesmith.common.ssm import put_string_parameter, fetch_string_parameter

helper = CfnResource()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ssm = boto3.client('ssm')

properties_schema = tolerant_schema({
    'Sequence': non_empty_string
})


def validate_properties(properties):
    return Box(properties_schema.validate(properties), camel_killer_box=True)


@helper.create
@helper.delete
def create(event, _):
    properties = validate_properties(resource_properties(event))
    physical_id = physical_resource_id(event, properties)

    value = next_value(properties)

    helper.Data.update({
        'ValueText': str(value),
        'Value': value
    })
    return physical_id


def next_value(properties):
    parameter_name = properties.sequence
    expression = fetch_string_parameter(ssm, parameter_name)
    n = put_string_parameter(ssm, parameter_name,
                             value=expression,
                             description=SSM_PARAMETER_DESCRIPTION)
    version = n['Version']
    calc = calculator(version - 1)
    return calc.parse(expression)


def physical_resource_id(event, properties):
    return '{0}-{1}'.format(logical_resource_id(event), properties.sequence)


@helper.delete
def delete(event, _):
    return cfn.physical_resource_id(event)


def handler(event, context):
    logger.info('event: %s', event)
    helper(event, context)
