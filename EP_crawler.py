from manager import log_manager
from manager import file_manager
from manager import web_driver_manager
from manager import translate_manager

from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from dataclasses import dataclass
import pandas as pd
import pyperclip
import datetime
import time
import re

@dataclass
class Product:
    code: str
    org_name: str
    name: str
    price: str
    dealer_price: str
    description: str
    trans_description: str
    images: list
    make: str
    model: str
    year: str
    
class Evotech_Crawler:
    def __init__(self, logger: log_manager.Logger):
        self.file_manager = file_manager.FileManager()
        self.logger = logger
        self.driver_manager = web_driver_manager.WebDriverManager(self.logger)
        self.driver_manager.create_driver(is_udc=True)
        self.driver_obj = self.driver_manager.drive_obj
        self.driver = self.driver_obj.driver
        self.file_manager.create_dir("./temp")
        self.file_manager.create_dir("./output")
        self.product_numbers = []
        self.products = []
        self.data = dict()
        self.data_init()

    def convert_to_lowercase_except_special_chars(self, input_string):
        # 영어 문자만 소문자로 변환
        english_chars = ''.join(c.lower() if c.isalpha() else c for c in input_string)
        return english_chars
        
    def data_init(self):
        self.data.clear()
        self.data["상품 코드"] = list()
        self.data["상품명 원본"] = list()
        self.data["상품명"] = list()
        self.data["가격"] = list()
        self.data["딜러가"] = list()
        self.data["대표 이미지"] = list()
        self.data["상세 이미지"] = list()
        self.data["설명"] = list()
        self.data["설명 번역"] = list()
        self.data["MAKE"] = list()
        self.data["MODEL"] = list()
        self.data["YEAR"] = list()
        
    def extract_between_strings(self, original_string, start_string, end_string):
        pattern = f"{re.escape(start_string)}(.*?){re.escape(end_string)}"
        match = re.search(pattern, original_string)
        if match:
            return match.group(1)
        else:
            return None


    def login(self, id="bikeonline.korea@gmail.com", pw="piston7759!!!!"):
        self.driver.maximize_window()
        url = "https://evotech-performance.com/account/login"
        self.driver.get(url)
        id_input = self.driver.find_element(By.ID, "CustomerEmail")
        id_input.click()
        pyperclip.copy(id)
        actions = ActionChains(self.driver)
        actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(5)
        
        pw_input = self.driver.find_element(By.ID, "CustomerPassword")
        pw_input.click()
        pyperclip.copy(pw)
        actions = ActionChains(self.driver)
        actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(5)

        submit_btn = self.driver.find_element(By.CLASS_NAME, "button.button-primary")
        submit_btn.click()

        time.sleep(10)
        self.driver.minimize_window()

        confirm_url = "https://evotech-performance.com/account"
        
        if self.driver.current_url != confirm_url:
            return False
        
        return True

    def save_item_in_database(self, item: Product):
        self.data["상품 코드"].append(item.code)
        self.data["상품명 원본"].append(item.org_name)
        self.data["상품명"].append(item.name)
        self.data["가격"].append(item.price)
        self.data["딜러가"].append(item.dealer_price)
        if len(item.images) != 0:
            self.data["대표 이미지"].append(item.images[0])
            self.data["상세 이미지"].append("|".join(item.images))
        else:
            self.data["대표 이미지"].append("")
            self.data["상세 이미지"].append("")
        self.data["설명"].append(item.description)
        self.data["설명 번역"].append(item.trans_description)
        self.data["MAKE"].append(item.make)
        self.data["MODEL"].append(item.model)
        self.data["YEAR"].append(item.year)

    def save_database_to_excel(self, output_name):
        self.file_manager.create_dir(f"./output/{output_name}")
        data_frame = pd.DataFrame(self.data)
        data_frame.to_excel(f"./output/{output_name}/{output_name}.xlsx", index=False)

    def get_account_info(self, path):
        data = pd.read_csv(path)
        id = data["ID"].to_list()[0]
        pw = data["PW"].to_list()[0]
        return id, pw

    def get_make_list_from_file(self, path):
        data = pd.read_csv(path)
        make_list = data["MAKE"].to_list()
        return make_list

    def get_start_info(self, path):
        data = pd.read_csv(path)
        start_make = data["start_make"].to_list()
        if len(start_make) == 0:
            return False 
        start_make = start_make[0]
        start_model = data["start_model"].to_list()[0]
        start_year = data["start_year"].to_list()[0]

        start_info = [start_make, start_model, start_year]
        return start_info
    
    def get_make_links(self, make_list):
        make_infos = []
        for make in make_list:
            make_conv = self.convert_to_lowercase_except_special_chars(make.replace(" ", "-"))
            make_url = f"https://evotech-performance.com/pages/{make_conv}-motorcycle-parts"
            make_infos.append([make_url, make])

        return make_infos
    
    def get_model_links(self, make_url):
        model_infos = []
        self.driver.get(make_url)
        link_elemnets = self.driver.find_elements(By.CLASS_NAME, "links")

        for link_elemnet in link_elemnets:
            model_url = link_elemnet.get_attribute("href")
            model_text = link_elemnet.text
            model_infos.append([model_url, model_text])

        return model_infos
    
    def get_year_links(self, model_url):
        year_infos = []
        self.driver.get(model_url)
        link_elemnets = self.driver.find_elements(By.CLASS_NAME, "links")

        for link_elemnet in link_elemnets:
            year_url = link_elemnet.get_attribute("href")
            year_text = link_elemnet.text
            year_infos.append([year_url, year_text])

        return year_infos
    
    def get_product_links(self, year_url):
        product_infos = []
        self.driver.get(year_url)
        if self.driver_obj.is_element_exist(By.CLASS_NAME, "product-name"):
            product_elements = self.driver.find_elements(By.CLASS_NAME, "product-name")
            for product_element in product_elements:
                product_info = product_element.find_element(By.TAG_NAME, "a")
                product_url = product_info.get_attribute("href")
                product_name = product_info.text
                product_name = product_name.split("\n")
                product_name = product_name[1]
                if "News And Updates" not in product_name:
                    self.logger.log_debug(f"Found item : {product_name}")
                    product_infos.append([product_url, product_name])

        return product_infos
    
    def get_product_detail(self, product_url, product_name, make, model, year, output_name, is_category_crawling=True):
        self.driver.get(product_url)
        price = self.driver.find_element(By.ID, "ComparePrice-").find_element(By.CLASS_NAME, "money").text
        dealer_price = self.driver.find_element(By.ID, "ProductPrice-").find_element(By.CLASS_NAME, "money").text
        code = "ep-" + self.driver.find_element(By.ID, "productSKU").text.split(":")[1][1:]
        description = self.driver.find_element(By.ID, "productDescriptionOutput").text.replace("\n", "|")

        img_elements = []
        if self.driver_obj.is_element_exist(By.CLASS_NAME, "image-carousel-container"):
            img_elements = self.driver.find_element(By.CLASS_NAME, "image-carousel-container").find_elements(By.TAG_NAME, "img")
            img_elements = img_elements[:len(img_elements) // 2]
        else:
            # 360 image
            img_container_elements = self.driver.find_elements(By.CLASS_NAME, "MagicToolboxSlide")
            for img_container_element in img_container_elements:
                img_elements.append(img_container_element.find_element(By.TAG_NAME, "img"))

        img_names = []
        img_cnt = 1
        for i in range(len(img_elements)):
            img_url = img_elements[i].get_attribute("src")
            if "thumbnail" not in img_url and "360%20logo_small" not in img_url:
                img_name = f"{code}_{img_cnt}"
                img_names.append(img_name + ".jpg")
                self.driver_manager.download_image(img_url, img_name, f"./output/{output_name}/images")
                img_cnt += 1
        
        year_text = year
        year_alter_text= ""
        make_model_str = ""
        org_name = product_name
        
        if is_category_crawling:        
            year_text = self.extract_between_strings(year, "(", ")")
            year_alter_text = year_text.replace(" ", "")
            make_model_str = year.split("(")[0][:-1]
        
            product_name = product_name.replace(f"{make_model_str} ", "")
            product_name = product_name.replace(f"{year_text}", "")
            product_name = product_name.replace(f"{year_alter_text}", "")
        
        product = Product(code=code, org_name=org_name, name=product_name, price=price, dealer_price=dealer_price, description=description,
                          trans_description=translate_manager.translator(self.logger, "en", "ko", description), 
                          images=img_names, make=make, model=model, year=year_text)
        
        self.save_item_in_database(product)

        self.logger.log_info(f"Product {product_name} crawling completed!")
    
    def start_keyword_crawling(self):
        now = datetime.datetime.now()
        year = f"{now.year}"
        month = "%02d" % now.month
        day = "%02d" % now.day
        output_name = f"{year+month+day}_Keyword_EP"
        self.file_manager.create_dir(f"./output/{output_name}")
        self.file_manager.create_dir(f"./output/{output_name}/images")
        
        data = pd.read_csv("./settings/keyword_list.csv")
        keyword_list = data["KEYWORD"].to_list()
        id, pw = self.get_account_info("./settings/account_setting.csv")

        login_res = self.login(id, pw)

        if login_res == False:
            self.logger.log_error(f"로그인에 실패했습니다. 계정 정보를 다시 확인 해주세요. 계정 정보가 올바르다면, 프로그램을 다시 실행 해주세요.")
            return
        
        for keyword in keyword_list:
            search_url = f"https://evotech-performance.com/search?type=product&q={keyword}"
            product_infos = self.get_product_links(search_url)
            for product_info in product_infos:
                product_url = product_info[0]
                product_name = product_info[1]
                self.get_product_detail(product_url, product_name, "", "", "", output_name, is_category_crawling=False)

            self.save_database_to_excel(output_name)
    
    def start_category_crawling(self):

        now = datetime.datetime.now()
        year = f"{now.year}"
        month = "%02d" % now.month
        day = "%02d" % now.day
        output_name = f"{year+month+day}_Category_EP"
        self.file_manager.create_dir(f"./output/{output_name}")
        self.file_manager.create_dir(f"./output/{output_name}/images")
        
        make_list = self.get_make_list_from_file("./settings/make_list.csv")
        start_info = self.get_start_info("./settings/start_setting.csv")
        id, pw = self.get_account_info("./settings/account_setting.csv")

        login_res = self.login(id, pw)

        if login_res == False:
            self.logger.log_error(f"로그인에 실패했습니다. 계정 정보를 다시 확인 해주세요. 계정 정보가 올바르다면, 프로그램을 다시 실행 해주세요.")
            return
        
        is_found_start_point = False
        if start_info == False:
            is_found_start_point = True
        
        make_infos = self.get_make_links(make_list)
        for make_info in make_infos:
            make_url = make_info[0]
            make_name = make_info[1]
            self.logger.log_info(f"Current make : {make_name}")

            model_infos = self.get_model_links(make_url)
            for model_info in model_infos:
                model_url = model_info[0]
                model_name = model_info[1]
                self.logger.log_info(f"Current model : {model_name}")
                
                year_infos = []
                temp_infos = self.get_year_links(model_url)
                temp_year_name = temp_infos[0][1]
                
                if "(" in temp_year_name and ")" in temp_year_name:
                    year_infos = self.get_year_links(model_url)
                else:
                    temp_infos = self.get_year_links(model_url)
                    for temp_info in temp_infos:
                        url = temp_info[0]
                        year_infos += self.get_year_links(url)
                
                for year_info in year_infos:
                    year_url = year_info[0]
                    year_name = year_info[1]
                    year = self.extract_between_strings(year_name, "(", ")")
                    self.logger.log_info(f"Current category (make / model / year) : {make_name} / {model_name} / {year_name}")
                    if not is_found_start_point and make_name == start_info[0] and model_name == start_info[1] and year_name == start_info[2]:
                        is_found_start_point = True
                    if is_found_start_point:
                        product_infos = self.get_product_links(year_url)
                        for product_info in product_infos:
                            product_url = product_info[0]
                            product_name = product_info[1]
                            self.get_product_detail(product_url, product_name, make_name, model_name, year_name, output_name)

                        self.save_database_to_excel(output_name)
