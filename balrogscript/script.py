#!/usr/bin/env python
"""Balrog script
"""
from copy import deepcopy
import json
import logging
import os
import sys

from balrogscript.task import (validate_task_schema, get_task,
                               get_upstream_artifacts, get_manifest,
                               get_task_server)


log = logging.getLogger(__name__)


def create_submitter(e, balrog_auth, config):
    from balrog.submitter.cli import NightlySubmitterV4, ReleaseSubmitterV4  # noqa: E402
    auth = balrog_auth

    if "tc_release" in e:
        log.info("Taskcluster Release style Balrog submission")

        complete_info = e['completeInfo']
        partial_info = e.get('partialInfo')
        submitter = ReleaseSubmitterV4(api_root=config['api_root'], auth=auth,
                                       dummy=config['dummy'])

        data = {
            'platform': e['platform'],
            'productName': e['appName'],
            'appVersion': e['appVersion'],
            'version': e['version'],
            'build_number': e['build_number'],
            'locale': e['locale'],
            'hashFunction': e['hashType'],
            'extVersion': e['extVersion'],
            'buildID': e['buildid'],
            'completeInfo': complete_info
        }
        if partial_info:
            data['partialInfo'] = partial_info
        return submitter, data

    elif "tc_nightly" in e:
        log.info("Taskcluster Nightly style Balrog submission")

        complete_info = e['completeInfo']
        partial_info = e.get('partialInfo')
        submitter = NightlySubmitterV4(api_root=config['api_root'], auth=auth,
                                       dummy=config['dummy'],
                                       url_replacements=e.get('url_replacements', []))

        data = {
            'platform': e["platform"],
            'buildID': e["buildid"],
            'productName': e["appName"],
            'branch': e["branch"],
            'appVersion': e["appVersion"],
            'locale': e["locale"],
            'hashFunction': e['hashType'],
            'extVersion': e["extVersion"],
            'completeInfo': complete_info
        }
        if partial_info:
            data['partialInfo'] = partial_info
        return submitter, data
    else:
        raise RuntimeError("Unknown Balrog submission style. Check manifest.json")


def usage():
    print >> sys.stderr, "Usage: {} CONFIG_FILE".format(sys.argv[0])
    sys.exit(2)


def update_config(config, server='default'):
    config = deepcopy(config)

    config['api_root'] = config['server_config'][server]['api_root']
    username, password = (config['server_config'][server]['balrog_username'],
                          config['server_config'][server]['balrog_password'])
    del(config['server_config'])
    return (username, password), config


def setup_logging(verbose=False):
    log_level = logging.INFO
    if verbose:
        log_level = logging.DEBUG

    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s",
                        stream=sys.stdout,
                        level=log_level)
    logging.getLogger("boto").setLevel(logging.WARNING)


def load_config(path=None):
    try:
        with open(path) as fh:
            config = json.load(fh)
    except (ValueError, OSError) as e:
        print >> sys.stderr, "Can't read config file {}!\n{}".format(path, e)
        sys.exit(5)
    except KeyError as e:
        print >> sys.stderr, "Usage: balrogscript CONFIG_FILE\n{}".format(e)
        sys.exit(5)
    return config


def setup_config(config_path):
    if config_path is None:
        if len(sys.argv) != 2:
            usage()
        config_path = sys.argv[1]

    config = load_config(config_path)
    return config


def main(name=None, config_path=None):
    if name not in (None, '__main__'):
        return

    config = setup_config(config_path)
    setup_logging(config['verbose'])

    task = get_task(config)
    validate_task_schema(config, task)

    server = get_task_server(task, config)
    balrog_auth, config = update_config(config, server)

    config['upstream_artifacts'] = get_upstream_artifacts(task)

    # hacking the tools repo dependency by first reading its location from
    # the config file and only then loading the module from subdfolder
    sys.path.insert(0, os.path.join(config['tools_location'], 'lib/python'))
    # Until we get rid of our tools dep, this import(s) will break flake8 E402
    from util.retry import retry  # noqa: E402

    # Read the manifest from disk
    manifest = get_manifest(config)

    for e in manifest:
        # Get release metadata from manifest
        submitter, release = create_submitter(e, balrog_auth, config)
        # Connect to balrog and submit the metadata
        retry(lambda: submitter.run(**release))


main(name=__name__)
