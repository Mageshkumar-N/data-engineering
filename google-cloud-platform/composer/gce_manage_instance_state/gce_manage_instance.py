from airflow import DAG
from airflow.providers.google.cloud.operators.compute \
    import ComputeEngineStartInstanceOperator, ComputeEngineStopInstanceOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator
from airflow.models.param import Param
import pathlib
import sys
from datetime import datetime, timedelta
import logging

base_path = str(pathlib.Path(__file__).resolve().parent)
sys.path.append(f'{base_path}/utils')
from util import get_env_config, get_run_config, success_handler, failure_handler

logger = logging.getLogger("airflow.task")

# DAG Default Args
ENV_CONFIG = get_env_config()
RUN_CONFIG = get_run_config()
EMAIL_RECIPIENTS = RUN_CONFIG.get('email_on_error')
PROJECT_ID = ENV_CONFIG.get('project_id')
ENV = ENV_CONFIG.get('env')
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': EMAIL_RECIPIENTS,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=1)
}

# DAG Run Details
SCHEDULE_INTERVAL = None
PROCESS_NAME = 'Compute Engine Manage Instance'
PROCESS_DESC = ''
DAG_PREFIX = f'{ENV}_' if ENV != "PROD" else ""

# DAG Object
dag = DAG(
    default_args=default_args,
    dag_id=f"{DAG_PREFIX}gce_manage_instance",
    description=PROCESS_DESC,
    schedule_interval=SCHEDULE_INTERVAL,
    start_date=datetime(year=2023, month=1, day=1, hour=0, minute=0, second=0),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=2,
    is_paused_upon_creation=True,
    # on_success_callback=success_handler,
    # on_failure_callback=failure_handler,
    params={
        'zone': Param(title='Zone',
                      description='Region of the Compute Engine Instance',
                      type='string',
                      default='us-west1-b'),
        'resource_id': Param(title='Instance Name',
                             description='Name of the GCE Instance to Start/Stop',
                             type='string',
                             default='hackathon'),
        'action': Param(title='Action',
                        description='Action to perform on the GCE Instance',
                        type='string',
                        default='stop')
    },
)

with dag:
    start = EmptyOperator(
        task_id='START_TASK'
    )

    gce_instance_start = ComputeEngineStartInstanceOperator(
        task_id='GCE_INSTANCE_START',
        project_id=PROJECT_ID,
        zone='{{params.zone}}',
        resource_id='{{params.resource_id}}',
    )

    gce_instance_stop = ComputeEngineStopInstanceOperator(
        task_id='GCE_INSTANCE_STOP',
        project_id=PROJECT_ID,
        zone='{{params.zone}}',
        resource_id='{{params.resource_id}}',
    )

    end = EmptyOperator(
        task_id='END_TASK',
        trigger_rule='none_failed'
    )

    action_decision = BranchPythonOperator(
        task_id='ACTION_DECISION',
        op_args=['{{params.action}}', ],
        python_callable=lambda action: 'GCE_INSTANCE_START' if action == 'start' else 'GCE_INSTANCE_STOP'
    )

start >> action_decision >> [gce_instance_start, gce_instance_stop] >> end
