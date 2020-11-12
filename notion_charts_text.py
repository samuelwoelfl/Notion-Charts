from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from notion.client import NotionClient
from notion.block import *
from notion.collection import *
from notion.user import *

from datetime import datetime
import time

print('getting Notion page...')

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
sheets_client = gspread.authorize(creds)


token = 'cd8da425c7db1922f62fb6f7fffde69cd874130211bed1ebe25722bb3226053483de5b05753c7aa2bd168fb3886c41db1999599d8feda244f5d80364be23da228a42f03e249342d56d67adfbdcb9'
tableurl = 'https://www.notion.so/samuelwoelfl/1bdab4520874431ab2baa3bae6f3aba2?v=19ba09f26eb8461b9fd2c99a29e90091'
pageurl = 'https://www.notion.so/samuelwoelfl/Smoking-Page-d8279f2b8015487ca08e5cd261f597ab'

# url = 'https://www.notion.so/samuelwoelfl/Freelance-Space-4fc251bb5b5c4e2fad04b1b659f40ee4'
# name = "Aufträge"
custom_start_cord = [3, 1]
custom_end_cord = [4, 11]
custom_cords = True
skip_non_numerical_values = True


class NotionAPI:
    def __init__(self, token):
        self.notion_client = NotionClient(token_v2=token)

    def delete_empty_columns(self, data):
        indexes = []
        for ri, r in enumerate(data[1:]):
            for ci, c in enumerate(r):
                if c == "" and ri == 0:
                    indexes.append(ci)
                elif c != "" and ci in indexes:
                    indexes.remove(ci)
        for ri, r in enumerate(data):
            for i in sorted(indexes, reverse=True):
                r.pop(i)
        # print(data)
        return data


    def get_data(self, tableurl):
        table_view = self.notion_client.get_collection_view(tableurl)
        other_data = table_view.collection.get_schema_properties()
        print(other_data)
        properties = []
        for p in table_view.collection.get_schema_properties():
            if p['id'] == 'title':
                properties.insert(0, p['name'])
            else:
                properties.append(p['name'])

        data = []
        data.append(properties)
        for row in table_view.collection.get_rows():
            row_title = row.title
            row_dict = row.get_all_properties()
            # print(row_title)
            row = []
            print(row_dict)
            for i in row_dict:
                print(i, ': ', row_dict[i])
                key = i
                value = row_dict[i]

                try:
                    value = value.start
                    value = value.strftime("%d.%m.%Y")
                    isDate = True
                except:
                    isDate = False


                if type(value) == list:
                    # print('ist ne liste')
                    if len(value) > 0:
                        # print('ist länger als 0')
                        try:
                            value[0].full_name
                            isuser = True
                        except:
                            isuser = False

                        try:
                            value[0].title
                            ispage = True
                        except:
                            ispage = False

                        if not isuser and not ispage:
                            if not value[0]:
                                # print('erstes value existiert nicht')
                                # print('""')
                                value = ""
                            else:
                                value = ", ".join(value)
                        elif isuser:
                            if value[0]:
                                users = []
                                for u in value:
                                    name = u.full_name
                                    users.append(name)
                                value = ", ".join(users)
                            else:
                                value = ""
                        else:
                            if value[0]:
                                titles = []
                                for t in value:
                                    title = t.title
                                    titles.append(title)
                                value = ", ".join(titles)
                            else:
                                value = ""
                    else:
                        value = ""

                try:
                    if value != True and value != False and not isDate:
                        value = float(value)
                        is_numerical = True
                except:
                    is_numerical = False

                if not value or value == "":
                    # print('""')
                    row.append("")
                elif not skip_non_numerical_values:
                    if value == row_title:
                        row.insert(0, value)
                    else:
                        row.append(value)
                elif is_numerical or value == row_title:
                    if value == row_title:
                        row.insert(0, value)
                    else:
                        row.append(value)
                else:
                    row.append("")

                print(f'{value}\n')

            data.append(row)
            # print('\n')


        print(data)
        data = self.delete_empty_columns(data)
        frame_id = [tableurl + '§' + str(len(data[0])) + '§' + str(len(data))]
        data.insert(0, frame_id)
        return data


    def insert_chart(self, pageurl):
        page = self.notion_client.get_block(pageurl)
        table_anchor = self.notion_client.get_block(tableurl)
        chart = page.children.add_new(EmbedBlock, width=900, heigh=500)
        chart.set_source_url("https://notion.vip/notion-chart/draw.html?config_documentId=1ZF36sYn-zKctS2ZhY7HAjRQWYpQm4ETx5CAx0UCV9og&config_sheetName=Tabelle1&config_dataRange=C1%3AE161&config_chartType=line&config_theme=lightMode&option_legend_position=bottom")
        chart.move_to(table_anchor, "after")


class NotionCharts:
    def __init__(self, notion_link, data_name, start_cord, end_cord):
        self.notion_link = notion_link
        self.data_name = data_name
        self.start_cord = start_cord
        self.end_cord = end_cord
        self.bot = webdriver.Firefox()

    def fetch_site(self):
        bot = self.bot
        bot.get(self.notion_link)

    def get_data_frame(self):
        bot = self.bot

        delay = 10
        try:
            e = WebDriverWait(bot, delay).until(EC.visibility_of_element_located((By.CLASS_NAME, 'notion-collection-item')))
        except TimeoutException:
            print('failed - Timeout')

        time.sleep(3)
        print('success\n')
        print('finding table...')

        frames = bot.find_elements_by_class_name('notion-collection_view-block')
        frames_final = []
        for f in frames:
            if f.value_of_css_property("position") == 'static':
                try:
                    height_of_first_child = f.find_elements_by_tag_name("div")[0].value_of_css_property("height")
                    if height_of_first_child == '42px':
                        frames_final.append(f)
                except:
                    pass

        tables_raw = bot.find_elements_by_class_name('notion-scroller')
        tables_final = []
        for t in tables_raw:
            if "vertical" not in t.get_attribute("class"):
                tables_final.append(t)

        # Find the right table
        for f in frames_final:
            inner = f.find_elements_by_css_selector('div, a')
            for i in inner:
                if inner.index(i) == 4:
                    name_of_table = i.text.strip()
                    # print(name_of_table)
                    if name_of_table == self.data_name:
                        index = frames_final.index(f)

        table = tables_final[index]
        table_header_row = []

        notion_table_view = table.find_element_by_tag_name('div')
        table_container = notion_table_view.find_element_by_tag_name('div')
        table_header_c1 = table_container.find_element_by_tag_name('div')
        table_header_c2 = table_header_c1.find_element_by_tag_name('div')
        table_header_row_raw = table_header_c2.find_elements_by_class_name('notion-table-view-header-cell')
        if custom_cords:
            for i in table_header_row_raw[self.start_cord[0] - 1 : self.end_cord[0]]:
                table_header_row.append(i.text.strip())
        else:
            for i in table_header_row_raw:
                table_header_row.append(i.text.strip())

        print('success\n')
        print('scraping data...')

        data = []
        data.append(table_header_row)
        rows = table.find_elements_by_class_name('notion-collection-item')
        if not custom_cords:
            self.start_cord = [1, 1]
            self.end_cord = [0, len(rows)]
        for r in rows[self.start_cord[1] - 1 : self.end_cord[1]]:
            row = []
            childs = r.find_elements_by_css_selector('*')
            childs_clean = []
            for c in childs:
                parent_elem_class = c.find_element_by_xpath("..").get_attribute('class')
                try:
                    if 'notion-collection-item' in parent_elem_class:
                        childs_clean.append(c)
                except:
                    pass
            if not custom_cords:
                self.end_cord = [len(childs_clean), 0]
            for c in childs_clean[self.start_cord[0] - 1 : self.end_cord[0]]:
                try:
                    content = c.text
                    if content == "":
                        row.append("")
                    else:
                        ch1 = content[0]
                        che = content[-1]
                        if che == '€' or che == '$' or che == '£' or che == '%':
                            content = content[:-1]
                        if ch1 == '€' or ch1 == '$' or ch1 == '£' or ch1 == '%':
                            content = content[1:]
                        try:
                            content = float(content)
                            isnumerical = True
                        except:
                            isnumerical = False
                        if not skip_non_numerical_values:
                            row.append(content)
                        elif isnumerical or childs_clean.index(c) == 0:
                            row.append(content)
                        else:
                            row.append("")
                    
                except:
                    pass
            data.append(row)

        frame_id = [self.notion_link + '§' + self.data_name + '§' + str(len(data[0])) + '§' + str(len(data))]
        data.insert(0, frame_id)
        print('success\n')
        # print(data)
        self.bot.close()
        return data


class GoogleSheets:
    def __init__(self):
        self.sheet = sheets_client.open("Notion Charts").get_worksheet(0)
        self.id = ""

    def write_row(self, row, index):
        self.sheet.insert_row(row, index)

    def write_frame_get_start(self, frame):
        print('transfer data to google sheets...')
        start = len(self.sheet.get_all_values()) + 2
        self.id = frame[0]
        self.write_row(self.id, start)
        count = start
        for r in frame[1:]:
            self.write_row(r, count + 1)
            count += 1
        print('success\n')
        return start


def get_range(start, id):
    indeces = []
    for i, ch in enumerate(id):
        if id[i] == '§':
            indeces.append(i)
    width = id[indeces[0] + 1:indeces[1]]
    height = id[indeces[1] + 1:]

    start_cord = 'A' + str(start + 1)
    endcolumn = chr(ord('@') + int(width))
    endrow = start + int(height)
    endcord = str(endcolumn) + str(endrow)
    return start_cord + "%3A" + endcord


def generate_chart_link(range, chart_type, stacked, theme, legend_position):
    print('generating link...')
    link = 'https://notion.vip/notion-chart/draw.html?config_documentId=1B3c20WmqMQMCCaSvw5PPMBHTdLm1F82HePtC-7b1QRI&config_sheetName=Tabellenblatt1&config_dataRange=' + range + "&config_chartType=" + chart_type + "&option_isStacked=" + stacked + "&config_theme=" + theme + "&option_legend_position=" + legend_position
    print('success\n')
    return link




# Notion = NotionCharts(url, name, custom_start_cord, custom_end_cord)
# Notion.fetch_site()
# data_frame = Notion.get_data_frame()



Notion = NotionAPI(token)
data_frame = Notion.get_data(tableurl)
print(data_frame)

# doc = GoogleSheets()
# start = doc.write_frame_get_start(data_frame)
# id = doc.id[0]
# range = get_range(start, id)


#Properties

#line, bar, column, donut, pie
chart_type = 'column'

#true, false
stacked = 'false'

#lightMode, darkMode
theme = 'lightMode'

#left, bottom
legend_position = 'bottom'
#
# link = generate_chart_link(range, chart_type, stacked, theme, legend_position)
# print(f'\n Link:\n {link}')





