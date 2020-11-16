import gspread
from oauth2client.service_account import ServiceAccountCredentials

from notion.client import NotionClient
from notion.block import *


# takes about 10sec

# -----------------------------
# Set up Notion Connection
# -----------------------------
token = 'cd8da425c7db1922f62fb6f7fffde69cd874130211bed1ebe25722bb3226053483de5b05753c7aa2bd168fb3886c41db1999599d8feda244f5d80364be23da228a42f03e249342d56d67adfbdcb9'
tableurl = 'https://www.notion.so/samuelwoelfl/8f649c46e7b44eb78804d892e69eca4f?v=07d2c483af0a4c03b302ea4df4d395c1'
pageurl = 'https://www.notion.so/samuelwoelfl/Freelance-Space-4fc251bb5b5c4e2fad04b1b659f40ee4'

# -----------------------------
# Set up Google Docs Connection
# -----------------------------

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
sheets_client = gspread.authorize(creds)




# -----------------------------
# Properties
# -----------------------------
# skip_non_numerical_values = True  # mostly necessary because notionvip charts will throw an error when getting text values
# chart_type = 'column'  # line, bar, column, donut, pie
# stacked = 'false'  # true, false
# theme = 'lightMode'  # lightMode, darkMode
# legend_position = 'bottom'  # left, bottom


# -----------------------------
# Notion Api Class
# -----------------------------
class NotionAPI:
    def __init__(self, token):
        self.notion_client = NotionClient(token_v2=token)

    # clears all the empty columns so notionvip can work better with the data
    @staticmethod
    def delete_empty_columns(data):
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
        return data

    # fetches your Notion database values
    def get_data(self, tableurl, skip_non_numerical_values):
        table_view = self.notion_client.get_collection_view(tableurl)
        properties = []
        for p in table_view.collection.get_schema_properties():
            if p['id'] == 'title':
                properties.insert(0, p['name'])
            elif p['type'] != 'formula' and p['type'] != 'rollup':
                properties.append(p['name'])

        # create data frame and append database properties
        data = [properties]

        for r in table_view.collection.get_rows():
            row_title = r.title
            row_dict = r.get_all_properties()
            row = []
            for i in row_dict:
                value = row_dict[i]

                try:
                    value = value.start
                    value = value.strftime("%d.%m.%Y")
                    is_date = True
                except:
                    is_date = False


                if type(value) == list:
                    if len(value) > 0:

                        try:
                            value[0].full_name
                            isuser = True
                        except:
                            isuser = False

                        try:
                            if type(value[0].title) != type(pow):
                                ispage = True
                            else:
                                ispage = False
                        except:
                            ispage = False

                        if not isuser and not ispage:
                            if value[0]:
                                value = ", ".join(value)
                            else:
                                value = ""
                        elif isuser or ispage:
                            if value[0]:
                                items = []
                                for z in value:
                                    try:
                                        item = z.full_name
                                    except:
                                        item = z.title
                                    items.append(item)
                                value = ", ".join(items)
                            else:
                                value = ""
                        else:
                            value = ""
                    else:
                        value = ""
                try:
                    if value != True and value != False and not is_date:
                        value = float(value)
                        is_numerical = True
                except:
                    is_numerical = False

                if not value or value == "":
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

            data.append(row)

        data = self.delete_empty_columns(data)
        frame_id = [tableurl + '§' + str(len(data[0])) + '§' + str(len(data))]
        data.insert(0, frame_id)
        return data

    # insert the created chart in notion
    def insert_chart(self, pageurl, embedurl):
        page = self.notion_client.get_block(pageurl)
        table_anchor = self.notion_client.get_block(tableurl)
        chart = page.children.add_new(EmbedBlock, width=900, height=400)
        chart.set_source_url(embedurl)
        chart.move_to(table_anchor, "after")


# -----------------------------
# Google Sheets Class
# -----------------------------
class GoogleSheets:
    def __init__(self):
        self.sheet = sheets_client.open("Notion Charts").get_worksheet(0)
        self.id = ""

    # writes one row in google doc
    def write_row(self, row, index):
        self.sheet.insert_row(row, index)

    # writes data frame to google doc and finds start row
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

# gets range of table for the link
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

# generates the link for the chart
def generate_chart_link(range, chart_type, stacked, theme, legend_position):
    print('generating link...')
    link = 'https://notion.vip/notion-chart/draw.html?config_documentId=1B3c20WmqMQMCCaSvw5PPMBHTdLm1F82HePtC-7b1QRI&config_sheetName=Tabellenblatt1&config_dataRange=' + range + "&config_chartType=" + chart_type + "&option_isStacked=" + stacked + "&config_theme=" + theme + "&option_legend_position=" + legend_position
    print('success\n')
    return link


# -----------------------------
# Fetch Notion data
# -----------------------------
# Notion = NotionAPI(token)
# data_frame = Notion.get_data(tableurl)

# -----------------------------
# Write it to Google Doc
# -----------------------------
# doc = GoogleSheets()
# start = doc.write_frame_get_start(data_frame)
# id = doc.id[0]
# range = get_range(start, id)

# -----------------------------
# Generate Link
# -----------------------------
# link = generate_chart_link(range, chart_type, stacked, theme, legend_position)
# print(f'\n Link:\n {link}')

# -----------------------------
# Instert Chart with Notion Embed
# -----------------------------
# Notion.insert_chart(pageurl, link)





