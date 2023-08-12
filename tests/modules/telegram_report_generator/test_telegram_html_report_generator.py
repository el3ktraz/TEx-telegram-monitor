"""Telegram Groups Scrapper Tests."""

import asyncio
import datetime
import shutil
import unittest
from configparser import ConfigParser
from typing import Dict
from unittest import mock

import pytz
from sqlalchemy import select, insert, delete
from telethon.tl.functions.messages import GetDialogsRequest

from TEx.core.dir_manager import DirectoryManagerUtils
from TEx.database.db_initializer import DbInitializer
from TEx.database.db_manager import DbManager
from TEx.database.telegram_group_database import TelegramGroupDatabaseManager, TelegramMessageDatabaseManager
from TEx.models.database.telegram_db_model import (
    TelegramGroupOrmEntity,
    TelegramMediaOrmEntity, TelegramMessageOrmEntity, TelegramUserOrmEntity,
)
from TEx.modules.execution_configuration_handler import ExecutionConfigurationHandler
from TEx.modules.telegram_messages_scrapper import TelegramGroupMessageScrapper
from TEx.modules.telegram_report_generator.telegram_html_report_generator import TelegramReportGenerator
from tests.modules.mockups_groups_mockup_data import base_groups_mockup_data, base_messages_mockup_data, \
    base_users_mockup_data


class TelegramGroupMessageScrapperTest(unittest.TestCase):

    def setUp(self) -> None:

        self.config = ConfigParser()
        self.config.read('../../config.ini')

        DirectoryManagerUtils.ensure_dir_struct('_data')
        DirectoryManagerUtils.ensure_dir_struct('_data/resources')
        DirectoryManagerUtils.ensure_dir_struct('_data/media')

        DbInitializer.init(data_path='_data/')

        # Reset SQLlite Groups
        DbManager.SESSIONS['data'].execute(delete(TelegramMessageOrmEntity))
        DbManager.SESSIONS['data'].execute(delete(TelegramGroupOrmEntity))
        DbManager.SESSIONS['data'].execute(delete(TelegramMediaOrmEntity))
        DbManager.SESSIONS['data'].commit()

        # Add Group 1 - Without Any Message
        TelegramGroupDatabaseManager.insert_or_update({
            'id': 1, 'constructor_id': 'A', 'access_hash': 'AAAAAA',
            'fake': False, 'gigagroup': False, 'has_geo': False,
            'participants_count': 1, 'restricted': False,
            'scam': False, 'group_username': 'UN-A',
            'verified': False, 'title': 'UT-01', 'source': 'UT-PHONE'
        })

        # Add Group 2 - With Previous Messages
        TelegramGroupDatabaseManager.insert_or_update({
            'id': 2, 'constructor_id': 'B', 'access_hash': 'BBBBBB',
            'fake': False, 'gigagroup': False, 'has_geo': False,
            'participants_count': 2, 'restricted': False,
            'scam': False, 'group_username': 'UN-b',
            'verified': False, 'title': 'UT-02', 'source': 'UT-PHONE'
        })
        TelegramMessageDatabaseManager.insert({
            'id': 55, 'group_id': 2, 'date_time': datetime.datetime.now(tz=pytz.utc),
            'message': 'Message 1', 'raw': 'Raw Message 1', 'from_id': None, 'from_type': None,
            'to_id': None, 'media_id': None
        })
        TelegramMessageDatabaseManager.insert({
            'id': 56, 'group_id': 2, 'date_time': datetime.datetime.now(tz=pytz.utc),
            'message': 'Message 2', 'raw': 'Raw Message 2', 'from_id': None, 'from_type': None,
            'to_id': None, 'media_id': None
        })
        TelegramMessageDatabaseManager.insert({
            'id': 57, 'group_id': 2, 'date_time': datetime.datetime.now(tz=pytz.utc),
            'message': 'Message 2', 'raw': 'Raw Message 2', 'from_id': None, 'from_type': None,
            'to_id': None, 'media_id': None
        })
        TelegramMessageDatabaseManager.insert({
            'id': 58, 'group_id': 2, 'date_time': datetime.datetime.now(tz=pytz.utc),
            'message': 'Message 3', 'raw': 'Raw Message 3', 'from_id': None, 'from_type': None,
            'to_id': None, 'media_id': None
        })

        DbManager.SESSIONS['data'].commit()

    def tearDown(self) -> None:
        DbManager.SESSIONS['data'].close()

    def test_run_generate_report_disabled(self):
        """Test Run Method for Scrap Telegram Groups as Disabled."""

        # Call Test Target Method
        target: TelegramReportGenerator = TelegramReportGenerator()
        args: Dict = {
            'config': 'unittest_configfile.config',
            'report_folder': '_report',
            'group_id': '*',
            'order_desc': True,
            'filter': None,
            'limit_days': 30,
            'report': False,
            'suppress_repeating_messages': True
        }
        data: Dict = {}

        with self.assertLogs() as captured:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                target.run(
                    config=self.config,
                    args=args,
                    data=data
                )
            )

    def test_run_generate_report(self):
        """Test Run Method for Scrap Telegram Groups."""

        # Call Test Target Method
        target: TelegramReportGenerator = TelegramReportGenerator()
        args: Dict = {
            'config': 'unittest_configfile.config',
            'report_folder': '_report',
            'group_id': '*',
            'order_desc': True,
            'filter': 'Message',
            'limit_days': 30,
            'report': True,
            'suppress_repeating_messages': True,
            'around_messages': 2
        }
        data: Dict = {}
        self.__load_execution_config(args, data)

        with self.assertLogs() as captured:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                target.run(
                    config=self.config,
                    args=args,
                    data=data
                )
            )

    def __load_execution_config(self, args, data):

        execution_configuration_loader: ExecutionConfigurationHandler = ExecutionConfigurationHandler()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            execution_configuration_loader.run(
                config=self.config,
                args=args,
                data=data
            )
        )
