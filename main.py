import telebot
import os
import requests
from pymongo import MongoClient
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

bot = telebot.TeleBot(os.getenv("TOKEN"))
url = f"mongodb+srv://atlas:{os.getenv('ATLAS')}@xmeme.2irtq.mongodb.net/cowin_alerts?retryWrites=true&w=majority"

# MONGO CONNECTION
try:
    client = MongoClient(url)
    db = client.cowin_alerts
except:
    print("[ERROR] Cannot connect to MongoDB")


def handleStates(message, states):
    state_id = int(message.text)
    if state_id not in states:
        msg = bot.send_message(message.from_user.id, "Please enter valid number")
        bot.register_next_step_handler(msg, lambda m: handleStates(m, states))
        return

    districts = {}
    districts_data = requests.get(
        f"https://www.cowin.gov.in/api/v2/admin/location/districts/{state_id}"
    ).json()["districts"]
    for districtObj in districts_data:
        districts[districtObj["district_id"]] = districtObj["district_name"]
    msg = "Select a district: \n"
    for district in districts:
        msg += str(district) + " - " + districts[district] + "\n"
    msg = bot.send_message(message.from_user.id, msg)
    bot.register_next_step_handler(msg, lambda m: handleDistricts(m, districts))


def handleDistricts(message, districts):
    district_id = int(message.text)
    if district_id not in districts:
        msg = bot.send_message(message.from_user.id, "Please enter valid number")
        bot.register_next_step_handler(msg, lambda m: handleDistricts(m, districts))
        return

    msg = "1 - 18+\n2 - 45+"
    msg = bot.send_message(message.from_user.id, msg)
    bot.register_next_step_handler(msg, lambda m: handleAgeGroup(m, district_id))


def handleAgeGroup(message, district_id):
    age_group = int(message.text)
    if age_group != 1 and age_group != 2:
        msg = bot.send_message(message.from_user.id, "Please enter valid number")
        bot.register_next_step_handler(msg, lambda m: handleAgeGroup(m, district_id))
        return
    timestamp = datetime.now()
    date = timestamp.strftime("%d-%m-%Y")
    final_url = f"https://www.cowin.gov.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={district_id}&date={date}"
    user_object = {
        "user_id": message.from_user.id,
        "url": final_url,
        "age_group": age_group,
    }
    print(user_object)


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    states = {}
    states_data = requests.get(
        "https://www.cowin.gov.in/api/v2/admin/location/states"
    ).json()["states"]
    for stateObj in states_data:
        states[stateObj["state_id"]] = stateObj["state_name"]
    msg = "Select a State: \n"
    for state in states:
        msg += str(state) + " - " + states[state] + "\n"
    msg = bot.send_message(message.chat.id, msg)
    bot.register_next_step_handler(msg, lambda m: handleStates(m, states))


if __name__ == "__main__":
    print("POLLING...")
    bot.polling()
