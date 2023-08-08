import os
import uuid
import boto3
import datetime


class EventLevel:
    INFO = "info"
    WARN = "warn"
    ERROR = "error"

domain = os.getenv("DOMAIN", "dev")
region = os.getenv("REGION", "us-west-2")
class JobEventDao():


    def __init__(self, *args, **kwargs):
        self.event_table = boto3.client('dynamodb', region_name=region).Table("netmind-job-event-{}".format(domain))

    def before_insert(self, item):
        if "createdAt" not in item or not item["createdAt"]:
            item["createdAt"] = str(datetime.utcnow())
        if "createdAtYear" not in item or not item["createdAtYear"]:
            item["createdAtYear"] = int(item["createdAt"].split("-")[0])
        if "createdBy" not in item or not item["createdBy"]:
            item["createdBy"] = "admin"

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
