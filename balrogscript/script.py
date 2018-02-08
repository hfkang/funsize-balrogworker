#!/usr/bin/env python
"""Balrog script
"""
from copy import deepcopy
import json
import logging
import os
import sys

from balrogscript.task import (
    get_manifest,
    get_task,
    get_task_action,
    get_task_server,
    get_upstream_artifacts,
    validate_task_schema,
)


log = logging.getLogger(__name__)


# create_submitter {{{1
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


# submit_release {{{1
def submit_release(task, config, balrog_auth):
    """Submit a release blob to balrog."""
    upstream_artifacts = get_upstream_artifacts(task)

    # Read the manifest from disk
    manifest = get_manifest(config, upstream_artifacts)

    for e in manifest:
        # Get release metadata from manifest
        submitter, release = create_submitter(e, balrog_auth, config)
        # Connect to balrog and submit the metadata
        retry(lambda: submitter.run(**release))


# schedule_release {{{1
def schedule_release(task, config, balrog_auth):
    """Schedule a release to ship on balrog channel(s)"""

    # credentials
    # -----------
    # api-root
    # (credentials-file)
    # username

    # script_config.json
    # ------------------
    # verbose

    # release_config / task defn
    # --------------------------
    # version
    # product
    # build-number

    # unknown
    # -------
    # rules
    # schedule-at
    # background-rate

    # properties
    # ----------
    # "properties": {
    #   "product": "firefox",
    #   "build_number": 1,
    #   "balrog_api_root": "https://balrog-admin.stage.mozaws.net/api",
    #   "appVersion": "59.0",
    #   "channels": "beta",
    #   "version": "59.0b2",
    #   "release_promotion": true,
    #   "script_repo_revision": "733530b0789bdf1d296bda66b8703c46c1672d36",
    #   "revision": "733530b0789bdf1d296bda66b8703c46c1672d36",
    #   "release_eta": "2018-01-26T02:15:00+00:00",
    #   "next_version": "59.0b3",
    #   "repo_path": "projects/maple"
    # },

    #     for _, channel_config in self.query_channel_configs():
    #         self._submit_to_balrog(channel_config)

    # def _submit_to_balrog(self, channel_config):
    #     dirs = self.query_abs_dirs()
    #     auth = os.path.join(os.getcwd(), self.config['credentials_file'])
    #     cmd = [
    #         sys.executable,
    #         os.path.join(dirs["abs_tools_dir"],
    #                      "scripts/build-promotion/balrog-release-shipper.py")]
    #     cmd.extend([
    #         "--api-root", self.config["balrog_api_root"],
    #         "--credentials-file", auth,
    #         "--username", self.config["balrog_username"],
    #         "--version", self.config["version"],
    #         "--product", self.config["product"],
    #         "--build-number", str(self.config["build_number"]),
    #         "--verbose",
    #     ])
    #     for r in channel_config["publish_rules"]:
    #         cmd.extend(["--rules", str(r)])
    #     if channel_config.get("schedule_asap"):
    #         # RC releases going to the beta channel have no ETA set for the
    #         # RC-to-beta push. The corresponding task is scheduled after we
    #         # resolve the push-to-beta human decision task, so we can schedule
    #         # it ASAP plus some additional 30m to avoid retry() to fail.
    #         schedule_at = datetime.utcnow() + timedelta(minutes=30)
    #         cmd.extend(["--schedule-at", schedule_at.isoformat()])
    #     elif self.config.get("schedule_at"):
    #         cmd.extend(["--schedule-at", self.config["schedule_at"]])
    #     if self.config.get("background_rate"):
    #         cmd.extend(["--background-rate", str(self.config["background_rate"])])

    #     self.retry(lambda: self.run_command(cmd, halt_on_failure=True),
    #                error_level=FATAL)

    # from balrog.submitter.cli import ReleaseScheduler
    # suffix = os.environ.get("BALROG_BLOB_SUFFIX")
    # scheduler = ReleaseScheduler(api_root, auth, suffix=suffix)
    # if args.backgroundRate:
    #     scheduler.run(args.product_name.capitalize(), args.version,
    #                   args.build_number, args.rule_ids, args.schedule_at, args.backgroundRate)
    # else:
    #     scheduler.run(args.product_name.capitalize(), args.version,
    #                   args.build_number, args.rule_ids, args.schedule_at)


# push_release {{{1
def push_release(task, config, balrog_auth):
    """Push a top-level release blob to balrog."""

    # credentials:
    # ------------
    # api-root
    # (credentials-file)
    # username

    # mozharness releases/updates_firefox_BRANCH.py:
    # ----------------------------------------------
    # requires-mirrors
    # rules-to-update

    # script_config.json
    # ------------------
    # dummy - do we want this per-task or per-instance?

    # release_config / task defn
    # --------------
    # version
    # app_version
    # build_number
    # product
    # platform

    # unknown
    # -------
    # channel
    # partial-update
    # download-domain
    # archive-domain
    # open-url
    # hash-function
    # verbose
    # complate-mar-filename-pattern
    # complate-mar-bouncer-product-pattern

    # channel_configs = [
    #     (n, c) for n, c in self.config["update_channels"].items() if
    #     n in self.config["channels"]
    # ]

    # "update_channels": {
    # for beta
    #     "beta": {
    #         "version_regex": r"^(\d+\.\d+(b\d+)?)$",
    #         "requires_mirrors": True,
    #         "patcher_config": "mozBeta-branch-patcher2.cfg",
    #         "update_verify_channel": "beta-localtest",
    #         "mar_channel_ids": [],
    #         "channel_names": ["beta", "beta-localtest", "beta-cdntest"],
    #         "rules_to_update": ["firefox-beta-cdntest", "firefox-beta-localtest"],
    #         "publish_rules": [32],
    #     },
    # for release
    #     "beta": {
    #         "version_regex": r"^(\d+\.\d+(b\d+)?)$",
    #         "requires_mirrors": False,
    #         "patcher_config": "mozBeta-branch-patcher2.cfg",
    #         "update_verify_channel": "beta-localtest",
    #         "mar_channel_ids": [
    #             "firefox-mozilla-beta", "firefox-mozilla-release",
    #         ],
    #         "channel_names": ["beta", "beta-localtest", "beta-cdntest"],
    #         "rules_to_update": ["firefox-beta-cdntest", "firefox-beta-localtest"],
    #         "publish_rules": [32],
    #         "schedule_asap": True,
    #     },
    #     "release": {
    #         "version_regex": r"^\d+\.\d+(\.\d+)?$",
    #         "requires_mirrors": True,
    #         "patcher_config": "mozRelease-branch-patcher2.cfg",
    #         "update_verify_channel": "release-localtest",
    #         "mar_channel_ids": [],
    #         "channel_names": ["release", "release-localtest", "release-cdntest"],
    #         "rules_to_update": ["firefox-release-cdntest", "firefox-release-localtest"],
    #         "publish_rules": [145],
    #     },
    # for devedition
    #     "aurora": {
    #         "version_regex": r"^.*$",
    #         "requires_mirrors": True,
    #         "patcher_config": "mozDevedition-branch-patcher2.cfg",
    #         # Allow to override the patcher config product name, regardless
    #         # the value set by buildbot properties
    #         "patcher_config_product_override": "firefox",
    #         "update_verify_channel": "aurora-localtest",
    #         "mar_channel_ids": [],
    #         "channel_names": ["aurora", "aurora-localtest", "aurora-cdntest"],
    #         "rules_to_update": ["devedition-cdntest", "devedition-localtest"],
    #         "publish_rules": [10],
    #     },
    # },

    # for _, channel_config in self.query_channel_configs():
    #     self._submit_to_balrog(channel_config)

    # def _submit_to_balrog(self, channel_config):
    #     dirs = self.query_abs_dirs()
    #     auth = os.path.join(os.getcwd(), self.config['credentials_file'])
    #     cmd = [
    #         sys.executable,
    #         os.path.join(dirs["abs_tools_dir"],
    #                      "scripts/build-promotion/balrog-release-pusher.py")]
    #     cmd.extend([
    #         "--api-root", self.config["balrog_api_root"],
    #         "--download-domain", self.config["download_domain"],
    #         "--archive-domain", self.config["archive_domain"],
    #         "--credentials-file", auth,
    #         "--product", self.config["product"],
    #         "--version", self.config["version"],
    #         "--build-number", str(self.config["build_number"]),
    #         "--app-version", self.config["appVersion"],
    #         "--username", self.config["balrog_username"],
    #         "--verbose",
    #     ])
    #     for c in channel_config["channel_names"]:
    #         cmd.extend(["--channel", c])
    #     for r in channel_config["rules_to_update"]:
    #         cmd.extend(["--rule-to-update", r])
    #     for p in self.config["platforms"]:
    #         cmd.extend(["--platform", p])
    #     for v, build_number in self.query_matching_partials(channel_config):
    #         partial = "{version}build{build_number}".format(
    #             version=v, build_number=build_number)
    #         cmd.extend(["--partial-update", partial])
    #     if channel_config["requires_mirrors"]:
    #         cmd.append("--requires-mirrors")
    #     if self.config["balrog_use_dummy_suffix"]:
    #         cmd.append("--dummy")

    #     self.retry(lambda: self.run_command(cmd, halt_on_failure=True))

    # from balrog.submitter.cli import ReleaseCreatorV4, ReleasePusher
    # partials = {}
    # if args.partial_updates:
    #     for v in args.partial_updates:
    #         version, build_number = v.split("build")
    #         partials[version] = {"buildNumber": build_number}

    # credentials = {}
    # execfile(args.credentials_file, credentials)
    # auth = (args.username, credentials['balrog_credentials'][args.username])
    # suffix = os.environ.get("BALROG_BLOB_SUFFIX")
    # creator = ReleaseCreatorV4(
    #     args.api_root, auth, dummy=args.dummy, suffix=suffix,
    #     complete_mar_filename_pattern=args.complete_mar_filename_pattern,
    #     complete_mar_bouncer_product_pattern=args.complete_mar_bouncer_product_pattern)
    # pusher = ReleasePusher(args.api_root, auth, dummy=args.dummy, suffix=suffix)

    # creator.run(
    #     appVersion=args.app_version,
    #     productName=args.product.capitalize(),
    #     version=args.version,
    #     buildNumber=args.build_number,
    #     updateChannels=args.channels,
    #     ftpServer=args.archive_domain,
    #     bouncerServer=args.download_domain,
    #     enUSPlatforms=args.platforms,
    #     hashFunction=args.hash_function,
    #     openURL=args.open_url,
    #     partialUpdates=partials,
    #     requiresMirrors=args.requires_mirrors)

    # pusher.run(
    #     productName=args.product.capitalize(),
    #     version=args.version,
    #     build_number=args.build_number,
    #     rule_ids=args.rules_to_update)


# usage {{{1
def usage():
    print >> sys.stderr, "Usage: {} CONFIG_FILE".format(sys.argv[0])
    sys.exit(2)


# setup_logging {{{1
def setup_logging(verbose=False):
    log_level = logging.INFO
    if verbose:
        log_level = logging.DEBUG

    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s",
                        stream=sys.stdout,
                        level=log_level)


# update_config {{{1
def update_config(config, server='default'):
    config = deepcopy(config)

    config['api_root'] = config['server_config'][server]['api_root']
    username, password = (config['server_config'][server]['balrog_username'],
                          config['server_config'][server]['balrog_password'])
    del(config['server_config'])
    return (username, password), config


# load_config {{{1
def load_config(path=None):
    try:
        with open(path) as fh:
            config = json.load(fh)
    except (ValueError, OSError, IOError) as e:
        print >> sys.stderr, "Can't read config file {}!\n{}".format(path, e)
        sys.exit(5)
    return config


# setup_config {{{1
def setup_config(config_path):
    if config_path is None:
        if len(sys.argv) != 2:
            usage()
        config_path = sys.argv[1]

    config = load_config(config_path)
    return config


# main {{{1
def main(name=None, config_path=None):
    if name not in (None, '__main__'):
        return

    config = setup_config(config_path)
    setup_logging(config['verbose'])

    task = get_task(config)
    validate_task_schema(config, task)

    server = get_task_server(task, config)
    balrog_auth, config = update_config(config, server)
    action = get_task_action(task, config)

    # hacking the tools repo dependency by first reading its location from
    # the config file and only then loading the module from subdfolder
    sys.path.insert(0, os.path.join(config['tools_location'], 'lib/python'))
    # Until we get rid of our tools dep, this import(s) will break flake8 E402
    from util.retry import retry  # noqa: E402

    if action == 'push':
        push_release(task, config, balrog_auth)
    elif action == 'schedule':
        schedule_release(task, config, balrog_auth)
    else:
        submit_release(task, config, balrog_auth)


main(name=__name__)
