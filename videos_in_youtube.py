import os
import time

import numpy as np
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service


class Learing:
    def __init__(
        self,
        second: int = 7,
        link_file: str = "Youtube Videos/links.csv",
        video_save_file: str = "Youtube Videos/will_videos.csv",
        passing_file: str = "Youtube Videos/passing_link.csv",
    ):
        assert link_file is not None
        self.link_file = link_file
        if os.path.exists(self.link_file):
            self.data = pd.read_csv(self.link_file)
        else:
            self.data = pd.DataFrame({"tag": [], "link": []})

        self.video_save_file = video_save_file
        if not os.path.exists(self.video_save_file):
            self.video_save = pd.DataFrame({"title": [], "link": [], "flag": []})
        else:
            self.video_save = pd.read_csv(self.video_save_file)

        self.passing_file = passing_file
        if not os.path.exists(self.passing_file):
            self.passing = pd.DataFrame({"tag": [], "link": []})
        else:
            self.passing = pd.read_csv(self.passing_file)

        self.browser = None
        self.second = second
        self.new_video = pd.DataFrame(columns=["title", "link"])
        self.new_passing = pd.DataFrame(columns=["tag", "link"])

    def first_visit(self, link: str):
        self.browser.get(link)
        time.sleep(np.random.randint(self.second))

        # ? browser scroll down (loading)
        prev_height = self.browser.execute_script("return document.documentElement.scrollHeight")
        while True:
            self.browser.execute_script("window.scrollBy(0, document.documentElement.scrollHeight);")
            time.sleep(np.random.randint(self.second))

            curr_height = self.browser.execute_script("return document.documentElement.scrollHeight")
            if curr_height == prev_height:
                try:
                    self.browser.find_element_by_name("more-res").click()
                    time.sleep(np.random.randint(self.second))
                except:
                    break
            prev_height = curr_height

    def collect_video_link(self, videos: list):
        new_video = {"title": [], "link": []}
        for video in videos:
            new_video["title"].append(video.get_attribute("title"))
            new_video["link"].append(video.get_attribute("href"))
        return pd.DataFrame(new_video)

    def browser_init(self):
        self.browser = webdriver.Edge(service=Service(executable_path="./Youtube Videos/msedgedriver.exe"))

    def browser_finish(self):
        self.browser.quit()

    def base_link_add(self, tags: list, links: list):
        if len(tags) != len(links):
            print("Tags and links have different lengths")
            return
        if np.any(~pd.Series(pd.Series(tags).unique()).isin(["list", "channel"])):
            print("Tags have other value")
            return
        new_base_link = pd.DataFrame({"tag": tags, "link": links})

        previous_length = len(self.data)
        self.data = pd.concat([self.data, new_base_link], ignore_index=True)
        self.data.drop_duplicates(inplace=True)
        if previous_length != len(self.data):
            self.part_link_add(new_base_link)

    def part_link_add(self, new_base_link: pd.DataFrame):
        self.link_add(new_base_link)

    def link_add(self, data: pd.DataFrame = None):
        if data is None:
            print("Adding link doesn't exist")
            return

        if self.browser is None:
            self.browser_init()

        for _, (tag, base_link) in data.iterrows():
            try:
                self.first_visit(base_link)

                if tag == "list":
                    # // //*[@id="video-title"]
                    links = self.browser.find_elements(By.XPATH, '//*[@id="video-title"]')
                elif tag == "channel":
                    # // //*[@id="view-more"]/a
                    elements = self.browser.find_elements(By.XPATH, '//*[@id="view-more"]/a')
                    links = [element.get_attribute("href") for element in elements]
                else:
                    # print("Tag is neither link or channel:", link)
                    self.new_passing = pd.concat([self.new_passing, pd.DataFrame({"tag": [tag], "link": [base_link]})], ignore_index=True)
                    continue

                for link in links:
                    self.first_visit(link)
                    videos = self.browser.find_elements(By.XPATH, '//*[@id="video-title"]')
                    self.new_video = pd.concat([self.new_video, self.collect_video_link(videos)], ignore_index=True)
            except:
                # print("Failed:", base_link)
                self.new_passing = pd.concat([self.new_passing, pd.DataFrame({"tag": [tag], "link": [base_link]})], ignore_index=True)

            time.sleep(np.random.randint(self.second))

    def total_link_check(self):
        self.link_add(self.data)

    def base_link_save(self):
        if not os.path.exists(self.link_file):
            self.data.to_csv(self.link_file, index=False)
        else:
            self.data.to_csv(self.link_file, mode="a", index=False, header=False)

    def save_file(self, base_save: bool = False):
        if base_save:
            self.base_link_save()
        if None in [self.video_save_file, self.passing_file]:
            return

        self.new_video["flag"] = False
        self.video_save = pd.concat([self.video_save, self.new_video], ignore_index=True)
        self.video_save.drop_duplicates(subset=self.video_save.columns.difference(["flag"]), inplace=True)
        self.video_save.to_csv(self.video_save_file, index=False)

        self.passing = pd.concat([self.passing, self.new_passing], ignore_index=True)
        self.passing.drop_duplicates(inplace=True)
        self.passing.to_csv(self.passing_file, index=False)


if __name__ == "__main__":
    learning = Learing()

    # * new link add
    # tags = [
    #     "channel",
    #     # "list",
    # ]
    # links = [
    #     "https://www.youtube.com/@doumcode/playlists",
    # ]
    # learning.base_link_add(tags, links)
    # learning.save_file(True)

    # * total link check
    learning.total_link_check()
    learning.save_file()

    learning.browser_finish()
