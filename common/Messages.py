class Messages(object):
    def __init__(self):
        self.OK = "ok"
        self.FAILED = "failed"

        self.INTERFACE_MUST_BE_IMPLEMENTED = "This method must be implemented"
        self.RESOURCE_NOT_FOUND_MESSAGE_TEMPLATE = '"{}" not found'
        self.UNKNOWN_ERROR = "Unknown error, {}"
        self.API_ACTION_NOT_FOUND = "action not found!"
        self.UNAUTHORIZED_REQUEST = (
            "unauthorized request, 'access_token' is empty or invalid"
        )
        self.S3_CODE_URI_ERROR = "Code file uri should be in the following format: 'https://*.s3.*.amazonaws.com/*/*'"


msg = Messages()
