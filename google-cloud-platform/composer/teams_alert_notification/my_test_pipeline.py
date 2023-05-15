import json
import pathlib
import sys
import requests
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import logging

base_path = str(pathlib.Path(__file__).resolve().parent)
sys.path.append(f'{base_path}/utils')
from util import get_env_config, get_run_config, success_handler, failure_handler

logger = logging.getLogger("airflow.task")

# dag default args
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
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

# dag run details
SCHEDULE_INTERVAL = None
PROCESS_NAME = 'Notifications'
PROCESS_DESC = ''
DAG_PREFIX = f'{ENV}_' if ENV != "PROD" else ""

# dag object
dag = DAG(
    default_args=default_args,
    dag_id="my_test_pipeline",
    description=PROCESS_DESC,
    schedule_interval=SCHEDULE_INTERVAL,
    start_date=datetime(year=2023, month=1, day=1, hour=0, minute=0, second=0),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=2,
    is_paused_upon_creation=True,
    on_success_callback=success_handler,
    on_failure_callback=failure_handler
)


def success_task():
    logger.info('Executing success_task')
    print("Success Task")


def failure_task():
    logger.info('Executing failure_task')
    raise Exception("Dummy Failure")


with dag:
    task1 = PythonOperator(task_id='success_task', python_callable=success_task)
    task2 = PythonOperator(task_id='failure_task', python_callable=failure_task)

task1 >> task2
