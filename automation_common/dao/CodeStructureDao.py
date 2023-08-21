from boto3.dynamodb.conditions import Attr, Key

try:
    from AwsServices import aws
    from Const import AwsDynamoDB, Env
    from DynamodbDao import DynamodbDao
    from errors.CustomExceptions import ResourceNotFoundException
    from Logging import get_logger
except ModuleNotFoundError:
    from boto3_layer.python.AwsServices import aws
    from boto3_layer.python.Const import AwsDynamoDB, Env
    from boto3_layer.python.DynamodbDao import DynamodbDao
    from boto3_layer.python.Logging import get_logger
    from webkit_layer.python.errors.CustomExceptions import ResourceNotFoundException
from automation_common.bean.domain.CodeStructureDo import CodeStructureDo
from automation_common.Messages import msg

logger = get_logger(__name__)


class CodeStructureDao(DynamodbDao):
    code_structure_table = aws.dynamodb().Table(
        AwsDynamoDB.CODE_STRUCTURE.format(Env.DOMAIN)
    )

    def __init__(self, *args, **kwargs):
        super(CodeStructureDao, self).__init__(*args, **kwargs)

    def update_by_id(self, id, **kwargs):
        expression, attribute_names, attribute_values = self.get_update_param(**kwargs)

        ret = self.code_structure_table.update_item(
            Key={"id": id},
            UpdateExpression="set " + ",".join(expression),
            ExpressionAttributeNames=attribute_names,
            ExpressionAttributeValues=attribute_values,
        )
        return ret

    def get_by_id(self, id) -> CodeStructureDo:
        response = self.code_structure_table.get_item(Key={"id": id})
        if "Item" not in response:
            raise ResourceNotFoundException(
                msg.RESOURCE_NOT_FOUND_MESSAGE_TEMPLATE.format(
                    'Job common config item for id "{}"'.format(id)
                )
            )

        job = CodeStructureDo(**response["Item"])
        return job

    """
    Get model code item
    """

    def get_by_s3_key(self, s3_key) -> CodeStructureDo:
        response = self.code_structure_table.query(
            KeyConditionExpression=Key("s3_key").eq(s3_key),
            IndexName="s3_key-index",
            Limit=1,
        )

        if "Items" in response:
            for item in response["Items"]:
                return CodeStructureDo(**item)

        raise ResourceNotFoundException(
            msg.RESOURCE_NOT_FOUND_MESSAGE_TEMPLATE.format("Model image item")
        )

    """
    Insert one job common config to dynamodb
    """

    def insert_one(self, item):
        self.before_insert(item)
        self.code_structure_table.put_item(Item=item)

    def delete_by_id(self, id):
        self.code_structure_table.delete_item(Key={"id": id})

    """
    Get all arguments
    """

    def get_all(self, **kwargs):
        filter_expression = Attr("is_del").ne(True)

        for key in kwargs:
            filter_expression = filter_expression & (
                Attr(key).is_in(kwargs[key])
                if isinstance(kwargs[key], list)
                else Attr(key).eq(kwargs[key])
            )

        scan_iterator = self.scan_item_iterator(
            table=self.code_structure_table,
            scan_kwargs={"FilterExpression": filter_expression},
            cls=CodeStructureDo,
        )
        result = []
        for item in scan_iterator:
            result.append(item)

        result.sort(key=lambda item: item.sort)

        return result


code_structure_dao = CodeStructureDao()
