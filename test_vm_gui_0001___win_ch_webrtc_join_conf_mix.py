import datetime
import os
import PageJoinConf
import page_webrtc_conf
from l import l
import allure
import pytest
from allure_commons.types import AttachmentType
import multiprocessing as mp
from helper_driver import DriverFactory
from report_generator2 import Report
import time
import json
import random


class TestWinJoinConf:
    @staticmethod
    def nodes_wait(ip):
        time.sleep(random.random())
        while True:
            time.sleep(4)
            with open('nodes.json', 'r+') as json_file:
                data = json.load(json_file)
                if not data[ip]:
                    data[ip] = 1
                    json_file.seek(0)
                    json.dump(data, json_file, indent=4)
                    # json_file.truncate()
                    break

    @staticmethod
    def nodes_close(ip):
        with open('nodes.json', 'r+') as json_file:
            data = json.load(json_file)
            data[ip] = 0
            json_file.seek(0)
            json.dump(data, json_file, indent=4)
            # json_file.truncate()

    def setup_test(self, ip):
        self.nodes_wait(ip)
        now = datetime.datetime.now()
        self.the_file_name_pattern = os.path.basename(__file__)[:-3] + "___result____" + now.strftime(
            "%Y-%m-%d___%H%M%S")
        self.server = l["server"]
        self.id = l["conf.id"]
        self.password = l["conf.ps"]
        self.name = l["conf.name"]
        self.join_result = False
        self.driver = DriverFactory.get_grid_driver(ip, 'win10', 'chrome')
        self.rg2 = Report(self.the_file_name_pattern, self.driver)
        self.e = mp.Event()
        p = mp.Process(target=self.rg2.take_screen, args=(self.e, str(ip + __name__)))
        p.start()
        self.ip = ip

    def teardown(self):
        self.rg2.make_report(self.join_result)
        self.driver.back()
        self.driver.quit()
        self.e.set()
        self.rg2.save(self.ip + __name__)
        self.nodes_close(self.ip)
        print('test finished'.upper())

    @pytest.mark.parametrize('ip', [
        l['win.10.auto1.executor.ip'],
        l['win.10.auto2.executor.ip'],
        l['win.10.auto3.executor.ip']
    ])
    @pytest.mark.parametrize('id', [
        ('chrome', 'TL-159'),
        ('firefox' 'TL-123')
    ])
    @allure.title('Windows, {browser}')
    @allure.epic('Basic Cases')
    @allure.feature('Join MIX Conference Windows')
    @allure.story('Windows WebRTC by Id / Password')
    @allure.severity('critical')
    def test_join_conf(self, ip, id):
        try:
            print(id)
            self.setup_test(ip)
            driver = self.driver
            with allure.step('Connected to {}'.format(ip)):
                pass
            with allure.step('Navigating conference joining page and entering by id and password'):
                page = PageJoinConf.PageJoinConf(driver)
                no_errors = page.join_conf_webrtc_chrome_without_errors(self.server, self.id, self.password, self.name)
                with allure.step('Make screenshot'):
                    allure.attach(self.driver.get_screenshot_as_png(), name='Screenshot',
                                  attachment_type=AttachmentType.PNG)
                with allure.step('Checking if joining successful'):
                    if no_errors:
                        with allure.step('Checking if tab_container element is displayed on page'):
                            page_conf = page_webrtc_conf.PageWebRTCConf(driver)
                            self.join_result = page_conf.check_join()
                            assert self.join_result == True
                    else:
                        assert False
        except Exception as e:
            with allure.step('Making fail screenshot'):
                allure.attach(self.driver.get_screenshot_as_png(), name='Fail',
                              attachment_type=AttachmentType.PNG)
            print('Error: {}'.format(e))
            assert False
        self.driver.back()
