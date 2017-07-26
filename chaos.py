#!/usr/bin/env python

import logging
import kubernetes
import os
import random
import time
import pytz
import json
import datetime

from kubernetes.client.rest import ApiException
from http import HTTPStatus
from fnmatch import fnmatch

KILL_FREQUENCY = int(os.environ.get('CHAOS_MONKEY_KILL_FREQUENCY_SECONDS', 300))
NAMESPACE_INCLUDES = set(os.environ.get('CHAOS_MONKEY_NAMESPACE_INCLUDES', '*').split(','))
POD_INCLUDES = set(os.environ.get('CHAOS_MONKEY_POD_INCLUDES', '*').split(','))
POD_EXCLUDES = set(os.environ.get('CHAOS_MONKEY_POD_EXCLUDES', '*').split(','))

LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

# No error handling, if things go wrong Kubernetes will restart for us!
kubernetes.config.load_incluster_config()
v1 = kubernetes.client.CoreV1Api()

def preparePodList():
    __pods = v1.list_pod_for_all_namespaces().items

    __include_ns = [x for x in __pods if any(fnmatch(x.metadata.namespace, p) for p in NAMESPACE_INCLUDES)]
    __include_pod = [x for x in __include_ns if any(fnmatch(x.metadata.name, p) for p in POD_INCLUDES)]
    __exclude_pod = [x for x in __include_pod if not any(fnmatch(x.metadata.name, p) for p in POD_EXCLUDES)]

    return __exclude_pod

while True:
    pods = preparePodList()

    if not pods:
        LOGGER.info("no pod found under the searc criteria: [NAMESPACE:%s] [POD_INCLUDED:%s] [POD_EXCLUDED:%s]. exit", 
            INCLUDE_NAMESPACE, INCLUDE_POD, EXCLUDE_POD)
        exit(0)    

    pod = random.choice(pods)

    LOGGER.info("Terminating pod %s/%s", pod.metadata.namespace, pod.metadata.name)
    event_name = "Chaos monkey kill pod %s" % pod.metadata.name
    #v1.delete_namespaced_pod(
    #    name=pod.metadata.name,
    #    namespace=pod.metadata.namespace,
    #    body=kubernetes.client.V1DeleteOptions(),
    #)
    event_timestamp = datetime.datetime.now(pytz.utc)
    try:
        event = v1.read_namespaced_event(event_name, namespace=pod.metadata.namespace)
        event.count += 1
        event.last_timestamp = event_timestamp
        v1.replace_namespaced_event(event_name, pod.metadata.namespace, event)
    except ApiException as e:
        error_data = json.loads(e.body)
        error_code = HTTPStatus(int(error_data['code']))
        if error_code == HTTPStatus.NOT_FOUND:
            new_event = kubernetes.client.V1Event(
                count=1,
                first_timestamp=event_timestamp,
                involved_object=kubernetes.client.V1ObjectReference(
                    kind="Pod",
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    uid=pod.metadata.uid,
                ),
                last_timestamp=event_timestamp,
                message="Pod deleted by chaos monkey",
                metadata=kubernetes.client.V1ObjectMeta(
                    name=event_name,
                ),
                reason="ChaosMonkeyDelete",
                source=kubernetes.client.V1EventSource(
                    component="chaos-monkey",
                ),
                type="Warning",
            )
            v1.create_namespaced_event(namespace=pod.metadata.namespace, body=new_event)
        else:
            raise
    time.sleep(KILL_FREQUENCY)