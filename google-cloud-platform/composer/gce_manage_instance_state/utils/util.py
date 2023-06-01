import json
import pathlib
import requests
import logging
from airflow.models import Variable

base_path = str(pathlib.Path(__file__).resolve().parent.parent)
ENV_CONFIG = {}
RUN_CONFIG = {}
ENV_CONFIG_PATH = f'{base_path}/config/env.json'
RUN_CONFIG_PATH = f'{base_path}/config/run_config.json'


def get_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)


def get_run_config():
    global RUN_CONFIG
    if not RUN_CONFIG:
        try:
            RUN_CONFIG = get_config(RUN_CONFIG_PATH)
        except Exception as e:
            print(e)
            raise Exception(f"Exception raised while reading run config file from path {RUN_CONFIG_PATH}")
    return RUN_CONFIG


def get_env_config():
    global ENV_CONFIG
    if not ENV_CONFIG:
        try:
            ENV_CONFIG = get_config(ENV_CONFIG_PATH)
        except Exception as e:
            print(e)
            raise Exception(f"Exception raised while reading environment config file from path {ENV_CONFIG_PATH}")
    return ENV_CONFIG


def format_sql(sql):
    env_config = ENV_CONFIG
    print(env_config)
    sql = sql.format(**env_config)
    return sql


def format_sql_from_path(sql_path):
    with open(sql_path, 'r') as f:
        sql = f.read()
    return format_sql(sql)


"""

success_handler() & failure_handler() are used as Callback Functions in the DAG to send alerts to the Teams Channel.

Pre-requisites: Set the below Airflow Variables to utilize this utility to receive Teams Alert Notifications.
    * webhook_url
    * project_id

"""

logger = logging.getLogger("airflow.task")


def send_notification(payload):
    webhook_url = Variable.get('webhook_url')
    logger.info(f'Webhook URL: {webhook_url}')

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))

    logger.info(f'Response Received from Teams Webhook: {response.text.encode("utf8")}')


def success_handler(context):
    logger.info('Executing on_success_callback')
    logger.info(f'Context received in success_handler: {context}')

    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": "Success Notification",
        "sections": [{
            "activityTitle": "Success Notification",
            "activitySubtitle": f"From project: {Variable.get('project_id')}",
            "activityImage": "https://cwiki.apache.org/confluence/download/attachments/145723561/airflow_white_bg.png?api=v2",
            "facts": [{
                "name": "Dag Name",
                "value": f"{context['dag'].dag_id}"
            }, {
                "name": "Run ID",
                "value": f"{context['run_id']}"
            }, {
                "name": "DAG Status",
                "value": "Success"
            }],
            "markdown": "true"
        }],
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "Go to Airflow Logs",
                "targets": [{
                    "os": "default",
                    "uri": f"{context['dag_run'].get_task_instance(context['task'].task_id).log_url}"
                }]
            },
            {
                "@type": "OpenUri",
                "name": "Go to Cloud Logging",
                "targets": [{
                    "os": "default",
                    "uri": f"https://console.cloud.google.com/logs/query;query=%20resource.type%3D%22cloud_composer_environment%22%20resource.labels.project_id%3D%22{Variable.get('project_id')}%22%20timestamp%3E%3D%22{context['execution_date'].strftime('%Y-%m-%dT%H:%M:%S.%fZ')}%22%20severity%3E%3DDEFAULT?project={Variable.get('project_id')}"
                }]
            }
        ]
    }

    logger.info(f'Success Payload: {payload}')

    send_notification(payload)


def failure_handler(context):
    logger.info('Executing on_failure_callback')
    logger.info(f'Context received in failure_handler: {context}')

    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": "Pipeline Notification",
        "sections": [{
            "activityTitle": "Failure Notification",
            "activitySubtitle": f"From project: {Variable.get('project_id')}",
            "activityImage": "https://cwiki.apache.org/confluence/download/attachments/145723561/airflow_white_bg.png?api=v2",
            "facts": [{
                "name": "Dag Name",
                "value": f"{context['dag'].dag_id}"
            }, {
                "name": "Run ID",
                "value": f"{context['run_id']}"
            }, {
                "name": "Task Name",
                "value": f"{context['task'].task_id}"
            }, {
                "name": "DAG Status",
                "value": "Failed"
            }, {
                "name": "Failure Reason",
                "value": f"{context['reason']}"
            }],
            "markdown": "true"
        }],
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "Go to Airflow Logs",
                "targets": [{
                    "os": "default",
                    "uri": f"{context['dag_run'].get_task_instance(context['task'].task_id).log_url}"
                }]
            },
            {
                "@type": "OpenUri",
                "name": "Go to Cloud Logging",
                "targets": [{
                    "os": "default",
                    "uri": f"https://console.cloud.google.com/logs/query;query=%20resource.type%3D%22cloud_composer_environment%22%20resource.labels.project_id%3D%22{Variable.get('project_id')}%22%20timestamp%3E%3D%22{context['execution_date'].strftime('%Y-%m-%dT%H:%M:%S.%fZ')}%22%20severity%3E%3DDEFAULT?project={Variable.get('project_id')}"
                }]
            }
        ]
    }

    logger.info(f'Failure Payload: {payload}')

    send_notification(payload)
