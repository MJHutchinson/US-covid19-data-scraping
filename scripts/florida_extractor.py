import os
import re
import json

import fitz
import warnings
import requests
import subprocess

import pandas as pd

from glob import glob
from shutil import copyfile
from os import system, mkdir
from os.path import basename, join, exists
from datetime import date, timedelta, datetime
from dateutil.parser import parse as parsedate
from bs4 import BeautifulSoup, SoupStrainer


def get_florida():
    # check existing assets
    # existing_assets = list(map(basename, glob("pdfs/florida/state_reports*.pdf")))
    with open("existing_assets_florida") as f:
        # https://stackoverflow.com/questions/3277503/how-to-read-a-file-line-by-line-into-a-list
        existing_assets = f.readlines()
        # you may also want to remove whitespace characters like `\n` at the end of each line
        existing_assets = [x.strip().split(" ")[-1] for x in existing_assets]

    headers = requests.utils.default_headers()
    url = "http://ww11.doh.state.fl.us/comm/_partners/covid19_report_archive/cases-monitoring-and-pui-information/state-report/"
    req = requests.get(url, headers)
    soup = BeautifulSoup(req.content, "html.parser")
    covid_links = []
    for links in soup.find_all("a"):
        link = links.get("href")
        if "state_reports_2" == link[:15]:
            pdf_name = basename(link)
            if pdf_name in existing_assets:
                continue
            covid_links.append(pdf_name)
            # check if pdf is already up to date

    print(covid_links)

    # download these assets
    #    api_base_url = "http://ww11.doh.state.fl.us/comm/_partners/covid19_report_archive"
    api_base_url = "http://ww11.doh.state.fl.us/comm/_partners/covid19_report_archive/cases-monitoring-and-pui-information/state-report"
    for pdf_name in covid_links:
        print(pdf_name, "DOWNLOAD")
        subprocess.run(
            [
                "wget",
                "--no-check-certificate",
                "-O",
                "pdfs/florida/{}".format(pdf_name),
                join(api_base_url, pdf_name),
            ]
        )
    print(existing_assets)
    # extract the latest data for each day
    existing_assets = glob("pdfs/florida/state_reports_2*.pdf")
    existing_assets.sort()
    # existing_assets = ["pdfs/florida/state_reports_latest_06_27.pdf"]
    usable_assets = {}
    for pdf_path in existing_assets:

        # if pdf_path == "pdfs/florida/state_reports_latest_06_20.pdf":
        #     continue
        pdf_base = basename(pdf_path)
        # pdf_date = None
        # tmp = re.search("[0-9]+-[0-9]+-[0-9]+", pdf_base)
        # print(pdf_base)
        # if tmp is not None:
        #     pdf_date = datetime.strptime(tmp.group(0), "%Y-%m-%d")
        # tmp = re.search("[0-9]+\\.[0-9]+\\.[0-9]{4}", pdf_base)
        # if tmp is not None:
        #     pdf_date = datetime.strptime(tmp.group(0), "%m.%d.%Y")
        # tmp = re.search("[0-9]+\\.[0-9]+\\.[0-9]{2}", pdf_base)
        # if tmp is not None:
        # pdf_date = datetime.strptime(tmp.group(0), "%m.%d.%y")
        # takes care of 20200603 types
        tmp = re.search("[0-9]{4}[0-9]{2}[0-9]{2}", pdf_base)
        if tmp is not None:
            pdf_date = datetime.strptime(tmp.group(0), "%Y%m%d")
            print(pdf_date)
        # # takes care of 06_03 types
        # tmp = re.search("[0-9]{2}_[0-9]{2}.pdf", pdf_base)
        # if tmp is not None:
        #     tmp = "2020_" + tmp.group(0).split(".")[0]
        #     pdf_date = datetime.strptime(tmp, "%Y_%m_%d")
        # # takes care of 0603 types
        # tmp = re.search("_[0-9]{2}[0-9]{2}.pdf", pdf_base)
        # if tmp is not None:
        #     tmp = "2020" + tmp.group(0).split(".")[0]
        #     pdf_date = datetime.strptime(tmp, "%Y_%m%d")
        # # takes care of aug_02 types
        # tmp = re.search("aug_[0-9]{2}.pdf", pdf_base)
        # if tmp is not None:
        #     tmp = "2020_08_" + tmp.group(0).split(".")[0][-2:]
        #     pdf_date = datetime.strptime(tmp, "%Y_%m_%d")
        # if pdf_date is None:
        #     raise ValueError(pdf_date)

        if (pdf_date >= datetime.strptime("2020-03-27", "%Y-%m-%d")) & (
            pdf_date != datetime.strptime("2020-08-05", "%Y-%m-%d")
        ):
            usable_assets[pdf_date.strftime("%Y-%m-%d")] = pdf_path
    print("USABLE: ", usable_assets)
    for day in usable_assets.keys():
        print(day, usable_assets[day])
        age_data = {}
        doc = fitz.Document(usable_assets[day])
        lines = doc.getPageText(1).splitlines()
        lines += doc.getPageText(2).splitlines()
        lines += doc.getPageText(3).splitlines()
        ## find key word to point to the age data table
        for num, l in enumerate(lines):
            if "years" in l:
                line_num = num
                age_data[lines[line_num]] = lines[line_num + 5]
                if len(age_data) == 10:
                    print(age_data)
                    break

        with open("data/{}/florida.json".format(day), "w") as f:
            json.dump(age_data, f)


if __name__ == "__main__":
    get_florida()
