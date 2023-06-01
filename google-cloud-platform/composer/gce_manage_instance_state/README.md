# <center> Manage GCE Instance State

The Airflow DAG helps users to either start or stop the VM instances manually on-demand basis based on the JSON configuration passed while triggering. 

This is helpful for users who cannot be given `compute.instances.start` and/or `compute.instances.stop` permissions due to organizational policies.

## Features

* Default JSON config is populated for ease of usage.
* Can be integrated with monitoring based triggers for automatic instance management.

## Usage

* Trigger the DAG w/ config.
* Edit the default JSON config as per requirement.
> **zone:** Pass the zone/region of the VM Instance. \
> **resource_id:** Pass the name of the VM Instance. \
> **action:** Pass either "start" or "stop" to manage the VM Instance state.
