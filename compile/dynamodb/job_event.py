import uuid

from boto3.dynamodb.conditions import Attr, Key

try:
    from AwsServices import aws
    from Const import AwsDynamoDB, Config, Env
    from DynamodbDao import DynamodbDao
    from errors.CustomExceptions import ResourceNotFoundException
except ModuleNotFoundError:
    from boto3_layer.python.AwsServices import aws
    from boto3_layer.python.Const import AwsDynamoDB, Config, Env
    from boto3_layer.python.DynamodbDao import DynamodbDao
    from webkit_layer.python.errors.CustomExceptions import ResourceNotFoundException

from common.bean.domain.JobEventDo import JobEventDo
from common.Messages import msg

class EventLevel:
    INFO = "info"
    WARN = "warn"
    ERROR = "error"

class JobEventDao(DynamodbDao):
    event_table = aws.dynamodb().Table(AwsDynamoDB.JOB_EVENT.format(Env.DOMAIN))

    def __init__(self, *args, **kwargs):
        super(JobEventDao, self).__init__(*args, **kwargs)

    def update_by_id(self, id, **kwargs):
        expression, attribute_names, attribute_values = self.get_update_param(**kwargs)

        ret = self.event_table.update_item(
            Key={"id": id},
            UpdateExpression="set " + ",".join(expression),
            ExpressionAttributeNames=attribute_names,
            ExpressionAttributeValues=attribute_values,
        )
        return ret

    def __handle_filter(self, **kwargs):
        filter_expression = Attr("is_del").ne(True)

        if "level" in kwargs:
            filter_expression = filter_expression & Attr("level").eq(kwargs["level"])

        if "content" in kwargs:
            filter_expression = filter_expression & Attr("content").contains(kwargs["content"])

        return filter_expression

    """

    payload: 
    {
        "limit": 4,
        "job_id": ""
        "LastEvaluatedKey": ""
    }

    """

    def get_page(self, **kwargs):
        # set a default size
        size = Config.DEFAULT_PAGE_SIZE
        if "limit" in kwargs:
            size = kwargs["limit"]

        scan_kwargs = {"ScanIndexForward": kwargs.get("scan_index_forward", False)}

        if kwargs.get("LastEvaluatedKey"):
            scan_kwargs["ExclusiveStartKey"] = kwargs.get("LastEvaluatedKey")

        scan_kwargs["KeyConditionExpression"] = Key("job_id").eq(kwargs["job_id"])
        scan_kwargs["FilterExpression"] = self.__handle_filter(**kwargs)

        event_do_list, lastEvaluatedKey = self._event_list_fetch(
            "job_id_createdAt-index", size, ["id", "job_id", "createdAt"], **scan_kwargs
        )
        result = {"count": len(event_do_list), "list": event_do_list}

        # Returns a payload that needs to be added for the next request to support the pagination
        if lastEvaluatedKey is not None:
            result["LastEvaluatedKey"] = lastEvaluatedKey
        return result

    def _event_list_fetch(self, index_name, size, last_evaluated_keys, **scan_kwargs):
        event_do_list = []

        lastEvaluatedKey = {}
        loop_search = True
        while loop_search:
            response = self.event_table.query(IndexName=index_name, **scan_kwargs)

            if "Items" in response:
                for index, item in enumerate(response["Items"]):
                    event_do_list.append(JobEventDo(**item))
                    if len(event_do_list) == size:
                        loop_search = False

                        if index <= len(response["Items"]) - 1:
                            # use last element as next "ExclusiveStartKey"
                            lastEvaluatedKey = {}
                            for key in last_evaluated_keys:
                                lastEvaluatedKey[key] = item[key]
                        break

            if "LastEvaluatedKey" not in response:
                loop_search = False
                break

            if lastEvaluatedKey is None:
                lastEvaluatedKey = response["LastEvaluatedKey"]
            scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

        return event_do_list, lastEvaluatedKey

    """
    Get all plans
    """

    def all_by_id(self, job_id, **kwargs):
        filter_expression = self.__handle_filter(**kwargs)

        scan_kwargs = {
            "IndexName": "job_id_createdAt-index",
            "FilterExpression": filter_expression,
            "KeyConditionExpression": Key("job_id").eq(job_id),
            "ScanIndexForward": kwargs.get("ScanIndexForward", False),
        }

        return self.query_item_iterator(
            self.event_table, JobEventDo, **scan_kwargs
        )

    """
    get specific job plan information
    """

    def get_by_id(self, id) -> JobEventDo:
        response = self.event_table.get_item(Key={"id": id})
        if "Item" not in response:
            raise ResourceNotFoundException(
                msg.RESOURCE_NOT_FOUND_MESSAGE_TEMPLATE.format("Job event")
            )

        return JobEventDo(**response["Item"])

    """
    Insert one job item to dynamodb
    """

    def insert_one(self, item):
        self.before_insert(item)
        self.event_table.put_item(Item=item)

    def quick_insert(self, job_id, job_status, level, content):
        self.insert_one(
            {
                "id": str(uuid.uuid4()),
                "job_id": job_id,
                "job_status": job_status,
                "level": level,
                "content": content,
            }
        )


job_event_dao = JobEventDao()
