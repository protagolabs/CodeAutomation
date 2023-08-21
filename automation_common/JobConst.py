import os


class YamlConst:
    K8S_JOB_MASTER_LABEL_KEY = "trainer_role"
    K8S_JOB_MASTER_LABEL_VALUE = "master"
    TF_WORKER_LABEL_KEY = "tf_worker"
    # when set 'spec.completionMode=Indexed', Kubernetes will set an associated completion index in env variables for each pod
    ENV_JOB_COMPLETION_INDEX = "JOB_COMPLETION_INDEX"
    TIME_ESTIMATE_PROCESS = {"key": "TIME_ESTIMATE_PROCESS", "value": "1"}
    USE_DDP = {"key": "USE_DDP", "value": "1"}
    TRAINER_MASTER = "trainer-master"


class MonitorConst:
    MONITOR_WANDB = "wandb"
    WANDB_URL = "https://wandb.ai/{}/{}/runs/{}"

    MONITOR_TENSORBOARD = "tensorboard"
    TENSORBOARD_FILE_EXT = ".png"


class CommandConst:
    PYTORCH_DDP_ARGUMENTS_PREFIX = "-m torch.distributed.run --nproc_per_node={{nproc_per_node}} --nnodes={{nnodes}} --node_rank={{node_rank}} {{master_addr}} --master_port {{master_service_port}} {{arguments}}"


class DirectoryConst:
    NETMIND_WORKSPACE = "/train"
    DEFAULT_CODE_LOCATION_PATTERN = "{}/code/{}"
    DEFAULT_DATA_LOCATION_PATTERN = "{}/datasets/{}"
    DEFAULT_MODEL_OUTPUT_DIR_PATTERN = "{}/checkpoint/{}"


class TimeConst:
    HIVEMIND_UPLOAD_INTERVAL = "1800"  # 10 minutes
    PROGRESS_REPORT_INTERVAL = 2 * 60  # progress upload time interval, unit seconds
    JOB_RETRIED_TIMES = 3
    ASSUMED_JOB_TIME_COST = (
        60 * 24
    )  # mock a time cost when job time cost estimate has not been finished
    # Training task progress update interval can not take more than "PROGRESS_REPORT_INTERVAL"/100 * "job estimate time cost" * "JOB_RUNNING_IDLE_EXCEED_TIMES" times
    # exp, if a job training estimate time cost is 10 hours, with default value set, the progress update interval can not take more than 5/100*(10*60)*2=60 minutes
    JOB_RUNNING_IDLE_EXCEED_TIMES = os.getenv("JOB_RUNNING_IDLE_EXCEED_TIMES", 2)
    JOB_WAITING_TIMEOUT = os.getenv(
        "JOB_WAITING_TIMEOUT", 30
    )  # timeout for job in waiting status, unit minutes
    JOB_ESTIMATING_TIMEOUT = os.getenv(
        "JOB_ESTIMATING_TIMEOUT", 30
    )  # timeout for job in waiting status, unit minutes
    JOB_POD_PENDING_TIMEOUT = os.getenv(
        "JOB_POD_PENDING_TIMEOUT", 10
    )  # timeout for job in waiting status, unit minutes
    JOB_PREPARING_TIMEOUT = (
        10 * 60
    )  # timeout for job in preparing timeout, unit minutes\
    # we consider that when job need less GPUs(especialy 1), the time cost between one step and average of total steps is small. Thus we need to increase estimate batches
    # as number of GPUs increased
    PYTORCH_TIMECOST_ESTIMATE_BATCH_PER_GPU = 10
    IMAGE_BUILD_ESITIMATE_COST = os.getenv("IMAGE_BUILD_ESITIMATE_COST", 15)
    ESTIMATE_TIME_COST_ESTIMATE_COST = os.getenv("ESTIMATE_TIME_COST_ESTIMATE_COST", 15)
    # JOB_WAITING_ESITIMATE_COST = os.getenv("JOB_WAITING_ESITIMATE_COST", 5)
    DEFAULT_JOB_ESTIMATE_COST = 5
    # aws support maximun 15 minutes delay message in sqs, so we use a counter to implement longer delay time
    PERIOD_CHARGE_HALF_HOUR_DELAY_COUNTER = 2
    PERIOD_CHARGE_HOUR_DELAY_COUNTER = 4
    BALANCE_CHECK_DELAY_SECONDS = 60 * 15

    BLOCK_CHAIN_TRANSACTION_CONFIRM_TIMEOUT = 60 * 15
    BLOCK_CHAIN_CHECK_DELAY = 5
    IGNORE_TRAINER_PERIOD_TIME = 10 * 60
    JOB_RUNNING_CHECK_DELAY = 60 * 3  # datadog event period 2 min
    REMOVE_JOB_FROM_RUNNING_DELAY = 60 * 15
    REMOVE_JOB_FROM_RUNNING_DELAY_COUNTER = 2


class Phase:
    ESTIMATE_TIME_COST = -1
    # HIVEMIND_LAUNCH_MONITOR = 1
    START_TRAINER = 0


class Regex:
    S3_CODE_FILE_URI = r"https://.*?\.s3\.{0,1}.*?\.amazonaws\.com/(.*)"


class FileLoc:
    S3 = "s3"


class ModelImageStatus:
    INIT = "init"
    READY = "ready"  # image building finished
    REBUILD = "rebuild"  # when model code changed, image should be rebuild too


class ArgumentType:
    STR = "str"
    INT = "int"
    BOOL = "bool"
    FLOAT = "float"


class NonVCJobType:
    TRAIN = "train"
    INFERENCE = "inference"


class YamlEnv:
    DATA_LOCATION = "DATA_LOCATION"


class TransactionEnum:
    exec_job = 0
    update_job = 1
    exec_debit = 2
    end_job = 3


class KubeSecret:
    AWS_CREDENTIALS = "aws-credentials"


class JobScheduleType:
    NON_VC_SYNC = "non_vc_sync"
    NON_VC_ASYNC = "non_vc_async"
    VC_ASYNC = "vc_async"


class SchedulePriority:
    NORMAL = 1
    HIGH = 2
    VC_JOB = 10
    ESTIMATE = 50
    RESERVED = 70  # job that has remaining peers wait to be deployed or jobs need to redeploy after a node down
