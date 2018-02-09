import os
from selenium import webdriver
from selenium.webdriver import FirefoxOptions
import argparse
import time
from getpass import getpass


def get_args():
    parse = argparse.ArgumentParser()
    parse.add_argument('--get-key', help="Generate an New API Key", action="store_true")
    parse.add_argument('--show-images', help="Show container image list which available", action="store_true")
    parse.add_argument('--webdriver', help="Specify the path of web driver. eg. geckodriver", type=str, default="")
    parse.add_argument('--pull', help="Pull specified image from repository", type=str)
    parse.add_argument('--debug', help="Use non-headless mode to see the actions for debug", action="store_true")
    parse.add_argument('--user', help="Provide user name for login", type=str, default="")
    parse.add_argument('--password', help="Password for login", type=str, default="")
    # add arguments of login user name and password
    return parse.parse_args()


def init_web_driver(debug, driver_path=None):
    drv_path = './geckodriver' if driver_path is None else driver_path
    if debug:
        engine = webdriver.Firefox(executable_path=drv_path)
    else:
        opts = FirefoxOptions()
        opts.add_argument('-headless')
        engine = webdriver.Firefox(firefox_options=opts, executable_path=drv_path)

    engine.get('https://ngc.nvidia.com/signin/email')
    time.sleep(2)
    return engine

def login_portal(engine, username, password):
    # Email Input Screen
    email_input_field = engine.find_element_by_xpath('//*[@id="email"]')
    email_input_field.send_keys(username)
    email_next_bt = engine.find_element_by_xpath('//*[@id="root"]/div/div/div/div/div/div[2]/form/div[2]/button')
    email_next_bt.click()

    # Password Input Screen
    time.sleep(2)
    pass_input_field = engine.find_element_by_xpath('//*[@id="password"]')
    pass_input_field.send_keys(password)
    login_bt = engine.find_element_by_xpath('//*[@id="root"]/div/div/div/div/div/div[2]/form/div[2]/button[2]')
    login_bt.click()

    # Getstart button  /html/body/div[2]/div/div/div/div/div[3]/div[2]/a
    time.sleep(2)
    try:
        get_start_bt = engine.find_element_by_xpath('/html/body/div[2]/div/div/div/div/div[3]/div[2]/a')
        get_start_bt.click()
    except:
        pass
    return engine

def auto_gen_api(engine):
    # Get 'Get API Key' Button and click
    time.sleep(2)
    get_api_bt = engine.find_element_by_xpath(
        '/html/body/div[2]/div/div/main/section/article[2]/div/div/div/div[1]/div[2]/a/button')
    get_api_bt.click()

    # Generate API Key
    time.sleep(2)
    generate_api_bt = engine.find_element_by_xpath(
        '/html/body/div[2]/div/div/main/section/article[2]/div/div/div[1]/div[2]/button')
    generate_api_bt.click()
    confirm_bt = engine.find_element_by_xpath('/html/body/div[3]/div/div/div/button[2]')
    confirm_bt.click()

    # parse response content
    time.sleep(2)
    api_key_div = engine.find_element_by_xpath(
        '/html/body/div[2]/div/div/main/section/article[2]/div/div/div[2]/div/div[2]/div[2]/div[2]/div')
    # print api_key_div.text
    api_key = api_key_div.text.split(':')[1].strip()
    return api_key


def get_docker_links(engine):
    """
    :type engine: selenium.webdriver.Firefox
    :param engine:
    :return:
    """
    # Expend the all of the sub-menu
    time.sleep(2)
    menus = engine.find_elements_by_class_name('rc-menu-submenu-title')
    for sub_menu in menus:
        if sub_menu.get_attribute('aria-expanded') == 'false':
            sub_menu.click()

    # Get Category

    # Get DockerImage <li> elements
    time.sleep(1)
    images = engine.find_elements_by_xpath("//li[contains(@class, 'rc-menu-item') and contains(@class, 'ui') and contains(@class, 'item') and contains(@class, 'modules-registry-components-RegistryTree-___registry_tree__item___3aMLF')]")
    for idx in xrange(len(images)):
        images = engine.find_elements_by_xpath(
            "//li[contains(@class, 'rc-menu-item') and contains(@class, 'ui') and contains(@class, 'item') and contains(@class, 'modules-registry-components-RegistryTree-___registry_tree__item___3aMLF')]")

        try:
            images[idx].click()
            time.sleep(2)
            pull_cmd = engine.find_element_by_xpath('/html/body/div[2]/div/div/main/section/article[2]/div/div/div/section/section/div/div/div').text
            app_name = pull_cmd.split('/')[2].split(':')[0]
            repo_name = pull_cmd.split('/')[0].split(' ')[-1]
            category = pull_cmd.split('/')[1]
            tag = pull_cmd.split('/')[2].split(':')[-1]
            image_table = engine.find_element_by_xpath('/html/body/div[2]/div/div/main/section/article[2]/div/div/div/section/section/section/div/div/div[2]')
            tag_nodes = image_table.find_elements_by_xpath('//div[contains(@role, "gridcell")]')
            all_tags = []
            for tag_node in tag_nodes:
                try:
                    title = tag_node.get_attribute('title').strip()
                    if title != "":
                        all_tags.append(title)
                except:
                    pass

            print("##############################################################")
            print("[Category]:          {}".format(category))
            print("[APP Name]:          {}".format(app_name))
            print("[Repository]:        {}".format(repo_name + "/" + category + "/" + app_name))
            print("[Latest Version]:    {}".format(tag))
            print("[Available Version]: {}".format(','.join(all_tags)))
            print("Use below format to pull the image:")
            print("# docker pull {}/{}/{}:{}".format(repo_name, category, app_name, "<Available Version>"))
            print(" ")
        except:
            pass


if __name__ == '__main__':
    args = get_args()
    if os.path.exists(args.webdriver):
        webdriver_path = args.webdriver
    else:
        webdriver_path = None

    if args.user.strip() == "":
        user_name = raw_input("User Name: ")

    if args.password.strip() == "":
        password = getpass("Password:")


    engine = init_web_driver(args.debug, driver_path=webdriver_path)
    engine = login_portal(engine, user_name, password)
    if args.show_images and not args.get_key:
        get_docker_links(engine)
        print('Done')
    elif args.get_key and not args.show_images:
        api_key = auto_gen_api(engine)
        print("Your new API Key is {}".format(api_key))
        print("Please use below command to login repository before pull images:")
        print(" # docker login nvcr.io")
        print(" Username:   $oauthtoken")
        print(" Password:   {}".format(api_key))
    else:
        print("No action will be taken")


    engine.close()
