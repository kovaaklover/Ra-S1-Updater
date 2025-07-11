import os
import json
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# DISCORD WEBHOOK URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1391768017301540905/r1twx2TJVsUUG-nlHOzQqr-SUP-6CFZBDEHfswsHbZGP1BoQ9Q6kmZ6YBDV_mj0OiG9o"

# ITERATE THROUGH STEAM USER IDS (ADD STEAM IDS AND NAMES AS SHOWN BELOW)
Steam_IDs = [76561198061001488, 76561199742787176, 76561199070216446, 76561199245857584]
Names = ['Veqzei', 'Kisen', 'Joe', 'Viagraa Falls']

Ranks = ["Unranked", "Diamond", "Master", "Grandmaster", "Immortal", "Archon", "Divine"]
Score_Dic = {}
session = requests.Session()

for i in range(len(Steam_IDs)):
    r = session.get(f"https://kovaaks.com/webapp-backend/benchmarks/player-progress-rank-benchmark?benchmarkId=534&steamId={Steam_IDs[i]}&page=0&max=100").json()

    Count = 4
    if Steam_IDs[i] not in Score_Dic:
        Score_Dic[Steam_IDs[i]] = [-2] * (52)
        Score_Dic[Steam_IDs[i]][1] = Names[i]

    # ITERATE THROUGH EACH CATEGORY
    for category_name, category_data in r["categories"].items():

        # ITERATE THROUGH EACH SCENARIO
        for scenario_name, scenario_data in category_data["scenarios"].items():
            Score_Dic[Steam_IDs[i]][Count] = scenario_data['scenario_rank']  # RANK
            Score_Dic[Steam_IDs[i]][Count+24] = scenario_data['score']/100  # SCORE
            Count += 1

session.close()

# FIGURE OUT POINTS
for key, values in Score_Dic.items():
    values[3] = sum((v + 6) for v in values[4:28] if v > -2)

# SORT POINTS
Score_Dic_S = dict(sorted(Score_Dic.items(), key=lambda item: (item[1][3]), reverse=True))

# ITERATE THROUGH ALL KEYS IN DICTIONARY
Count = 0
for key, values in Score_Dic_S.items():
    RankL = values[4:28]

    # CALCULATE RANKS
    for i in range(0, 7):
        if max(RankL[0:4]) >= i and max(RankL[4:8]) >= i and max(RankL[8:12]) >= i and max(RankL[12:16]) >= i and max(RankL[16:20]) >= i and max(RankL[20:24]) >= i:
            values[2] = Ranks[i]
        if min(RankL) >= i and i >= 0:
            values[2] = Ranks[i] + " Complete"

    # COUNT OF RELEVANT ENTRIES
    if values[24] != -2:
        Count += 1
        values[0] = Count

    # CONVERT RANKL TO ACTUAL RANKS (NUMBERS TO NAMES)
    for i in range(len(RankL)):
        RankL[i] = Ranks[RankL[i]]

    values[4:28] = RankL

# SHEET HEADERS
header = ['SteamID','Place','Player','Rank','Points', '1w4ts reload','Wide Wall 3 Targets','voxTS Static Click rAim','1w6t NQS Raspberry',
          'Bounce 180 rAim','Pasu Reload Goated', 'Popcorn Goated rAim', 'ToonsClick rAim',
          'PGTI rAim', 'Smoothbot rAim', 'Air Angelic', 'Controlsphere rAim',
          'fuglaaXY Reactive rAim', 'Air Small 3478 rAim', 'MFSI rAim', 'Smooth Thin Strafes Raspberry',
          'PatCircleSwitch rAim', 'Pokeball Wide rAim', 'voxTS rAim', 'devTS Goated rAim',
          'Bounce 180 Tracking Small', 'kinTS rAim', 'Pasu Track Smaller rAim', 'ToonsTS rAim',
          '1w4ts reload S','Wide Wall 3 Targets S','voxTS Static Click rAim S','1w6t NQS Raspberry S',
          'Bounce 180 rAim S','Pasu Reload Goated S', 'Popcorn Goated rAim S', 'ToonsClick rAim S',
          'PGTI rAim S', 'Smoothbot rAim S', 'Air Angelic S', 'Controlsphere rAim S',
          'fuglaaXY Reactive rAim S', 'Air Small 3478 rAim S', 'MFSI rAim S', 'Smooth Thin Strafes Raspberry S',
          'PatCircleSwitch rAim S', 'Pokeball Wide rAim S', 'voxTS rAim S', 'devTS Goated rAim S',
          'Bounce 180 Tracking Small S', 'kinTS rAim S', 'Pasu Track Smaller rAim S', 'ToonsTS rAim S'
          ]

# GOOGLE SHEETS API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# JSON CREDENTIAL FILE PATH (NEED FOR GITHUB ACTION)
creds_dict = json.loads(os.getenv('GSPREAD_CREDENTIALS'))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

# AUTHORIZE THE CLIENT
client = gspread.authorize(creds)

# OPEN GOOGLE SHEETs
sheet = client.open('S1_RA').worksheet('Discord Ranks')
sheet1 = client.open('S1_RA').worksheet('History')

# READ IN ALL OLD DATA TO A DICTIONARY
all_values = sheet.get_all_values()
old_data_dict = {}
for row in all_values[1:]:  # skip the header row at index 0
    key = int(row[0])         # first column as key
    values = row[1:]     # rest of the columns as list of values
    old_data_dict[key] = values

# READ ALL CHANGE DATA TO A LIST
change_rows = sheet1.get_all_values()

# ITERATE THROUGH NEW DICTIONARY TO CHECK FOR CHANGES IN RANK OR SCORE
last_row = change_rows[-1]
it = int(last_row[-1]) + 1

# FUNCTION TO SEND DISCORD NOTIFICATION
def send_discord_notification(row):
    try:
        player_name = row[0]
        change_type = row[1]
        new_value = row[2]
        
        # Create a formatted message
        if "Place Increase" in change_type:
            message = f"**{player_name}** climbed to **#{new_value}**!"
            color = 0x00ff00  
        elif "Place Decrease" in change_type:
            message = f"**{player_name}** dropped to **#{new_value}**"
            color = 0xff0000  
        elif "Overall Rank Increase" in change_type:
            message = f"**{player_name}** achieved **{new_value}** rank!"
            color = 0xffd700  
        elif "Rank Increase" in change_type:
            scenario = change_type.replace(": Rank Increase!", "")
            message = f"**{player_name}** improved in **{scenario}** to **{new_value}**!"
            color = 0x0099ff  
        elif "Score Increase" in change_type:
            scenario = change_type.replace(": Score Increase!", "")
            message = f"**{player_name}** set a new high score in **{scenario}**: **{new_value}**!"
            color = 0x9932cc  
        else:
            message = f"ERROR: **{player_name}**: {change_type} - {new_value}"
            color = 0x808080  
        
        #Discord embed payload
        payload = {
            "embeds": [{
                "title": "RankAim S1 Progress Update",
                "description": message,
                "color": color,
                "timestamp": None,
                "footer": {
                    "text": "RankAim S1 Tracker"
                }
            }]
        }
        
        #send to webhook
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        
        if response.status_code == 204:
            print(f"✅ Discord notification sent for {player_name}")
        else:
            print(f"❌ Failed to send Discord notification: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error sending Discord notification: {e}")
# CHECK FOR CHANGES
for steam_id, values in Score_Dic_S.items():
    if steam_id in old_data_dict:

        # SEE IF PLACE CHANGED
        if int(old_data_dict[steam_id][0]) != values[0]:
            if values[0] > int(old_data_dict[steam_id][0]):
                row = [values[1], 'Place Increase!', values[0], it]
                change_rows.append(row)
                send_discord_notification(row)
            else:
                row = [values[1], 'Place Decrease', values[0], it]
                change_rows.append(row)
                send_discord_notification(row)

        # SEE IF RA RANK CHANGED
        if old_data_dict[steam_id][2] != values[2]:
            row = [values[1], 'Overall Rank Increase!', values[2], it]
            change_rows.append(row)
            send_discord_notification(row)

        # SEE IF POINT CHANGED
    #    if int(old_data_dict[steam_id][3]) != values[3]:
    #        row = [values[1], 'Point Increase!', values[3], it]
    #        change_rows.append(row)

        # SEE IF A RANK CHANGED
        for i in range(4, 28):
            if old_data_dict[steam_id][i] != values[i]:
                row = [values[1], f'{header[i+1]}: Rank Increase!', values[i], it]
                change_rows.append(row)
                send_discord_notification(row)

        # SEE IF SCORE CHANGED
        for i in range(4, 28):
            if float(old_data_dict[steam_id][i+24]) != values[i+24]:
                row = [values[1], f'{header[i+1]}: Score Increase!', values[i+24], it]
                change_rows.append(row)
                send_discord_notification(row)


# CLEAR EXISTING DATA IN GOOGLE SHEET
sheet.clear()
#sheet1.clear()

# WRITE HEADERS TO FIRST ROW
sheet.append_row(header)

# SEND DATA FROM DICTIONARY TO ARRAY
rows_to_update = []
for steam_id, values in Score_Dic_S.items():
    row = [str(steam_id)] + values
    rows_to_update.append(row)


# UPDATE GOOGLE SHEET WITH ALL ARRAY DATA
start_cell = 'A2'
sheet.update(rows_to_update, start_cell)

# UPDATE GOOGLE SHEET WITH SCORE CHANGES
start_cell = 'A1'
sheet1.update(change_rows, start_cell)

