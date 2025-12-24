from datetime import date
import json
import re

from browser import document, ajax


SHEET_ID = '1vPgkbqdmYQg1y20jKJkr1IqACG0lSaeclUF3csRZ3so'
URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:json'
SEARCH_PATTERN = r'google\.visualization\.Query\.setResponse\((.*)\);'

DATA = dict()


def parse_gs_date(text):
    """
    Convert 'Date(2025, 11, 25)' → '2025-12-25'
    """
    expression_match = re.match(r"Date\((\d+),\s*(\d+),\s*(\d+)\)", text)

    if not expression_match:
        return text  # not a date, return as-is

    year, month, day = map(int, expression_match.groups())
    month += 1  # Google Sheets uses zero-based months
    date_value = date(year, month, day).isoformat()

    return date_value


def collect_sheet_data(sheet_data):
    rows = sheet_data['table']['rows']
    cols = sheet_data['table']['cols']

    for row in rows:
        entry = {}

        for col, cell in zip(cols, row['c']):
            key = col['label'] or col['id']

            if not cell or cell['v'] is None:
                continue

            value = cell['v']
            entry[key] = parse_gs_date(value)

        DATA[entry['player_id']] = entry
        DATA[entry['player_id']].pop('player_id', None)


def process_google_sheet(request):
    if request.status != 200:
        document['output'].html += f'\nError: {request.status}'
        return

    match = re.search(SEARCH_PATTERN, request.text, re.S)
    sheet_data = json.loads(match.group(1))
    collect_sheet_data(sheet_data)

    document['output'].html += f'\nBanned users loaded: {len(DATA)}'


def request_data():
    document['output'].html += f'Requesting Google Sheet data...'
    request = ajax.Ajax()
    request.bind('complete', process_google_sheet)
    request.open('GET', URL, True)
    request.send()


def check_player(event=None):
    player_id = str(document["player_id"].value)

    if player_id not in DATA:
        document['output'].html += f'\n\nPlayer [<b>{player_id}</b>] is <b><span style="color: green;">OK</span></b>'
        return

    document['output'].html += f'\n\nPlayer [<b>{player_id}</b>] is <b><span style="color: red;">BANNED!!!</span></b>\n'

    for key, value in DATA[player_id].items():
        document['output'].html += f'\n<b>{key}</b>: {value}'
