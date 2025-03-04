# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 NXP
#
# SPDX-License-Identifier: MIT


import logging
import os
import sys

import flatdict
import yaml

# pylint: disable=too-few-public-methods


class Config:
    @staticmethod
    def parse(fc_path):
        config_path = os.environ.get("FC_CONFIG_PATH", os.path.join(fc_path, "config"))
        cfg_file = os.path.join(config_path, "cfg.yaml")

        try:
            with open(cfg_file, "r", encoding="utf-8") as cfg_handle:
                cfg = yaml.load(cfg_handle, Loader=yaml.FullLoader)
        except FileNotFoundError as error:
            logging.error(error)
            logging.error("Put releated configs in %s", config_path)
            logging.error(
                "Instead, you could also set `FC_CONFIG_PATH` to override the default path."
            )
            sys.exit(1)

        raw_managed_resources = cfg["managed_resources"]
        if isinstance(raw_managed_resources, str):
            if not os.path.isabs(raw_managed_resources):
                raw_managed_resources = os.path.join(config_path, raw_managed_resources)
            try:
                with open(
                    raw_managed_resources, "r", encoding="utf-8"
                ) as resources_handle:
                    raw_managed_resources = yaml.load(
                        resources_handle, Loader=yaml.FullLoader
                    )
            except FileNotFoundError as error:
                logging.error(error)
                sys.exit(1)

        Config.raw_managed_resources = raw_managed_resources

        Config.managed_resources = flatdict.FlatterDict(raw_managed_resources).values()
        Config.managed_resources_farm_types = {}
        for farm_type, raw_managed_resource in raw_managed_resources.items():
            Config.managed_resources_farm_types.update(
                {
                    resource: farm_type
                    for resource in flatdict.FlatterDict(raw_managed_resource).values()
                }
            )

        Config.registered_frameworks = cfg["registered_frameworks"]
        Config.frameworks_config = cfg["frameworks_config"]
        Config.priority_scheduler = cfg.get("priority_scheduler", False)
        Config.api_server = cfg["api_server"]

        default_framework_strategies = [
            framework
            for framework in Config.registered_frameworks
            if Config.frameworks_config[framework].get("default", False)
        ]
        default_framework_number = len(default_framework_strategies)
        if default_framework_number > 1:
            logging.fatal("Fatal: at most one default framework could be specifed!")
            sys.exit(1)

        Config.default_framework = (
            None if default_framework_number == 0 else default_framework_strategies[0]
        )
