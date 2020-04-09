# Imports

import os
import json
import time
import base64
import config
import requests


def auth_client(msg_broker_base_url, user, pwd):
    """
    Authorise client with the server.
    Returns a JWT token on success, None otherwise.
    """
    auth_url = f"{msg_broker_base_url}/auth"
    response = requests.post(auth_url, json={"username": user, "password": pwd})
    if response.status_code != 200:
        print("coudn't authenticate")
        return None

    auth_token = response.json()["access_token"]
    return auth_token


def post_data(data, msg_broker_base_url, auth_token=None):
    """ Send data to remote server
        returns True on success, reises an Exception otherwise
        :param data: python list with measurements
        :param auth_token: string; JWT token for auth.
    """

    if not auth_token:
        raise Exception("No auth token - can't send data")

    post_url = f"{msg_broker_base_url}/post-message"
    response = requests.post(
        post_url,
        headers={
            "Authorization": f"JWT {auth_token}",
            "Content-Type": "application/json",
        },
        json={"data": data},
    )
    return response.status_code == 200


def remove_files(base_path, directories):
    for dirctr in directories:
        path = "{0}/{1}".format(base_path, dirctr)
        for root, dirs, files in os.walk(path):
            for file in files:
                os.remove(os.path.join(root, file))


def wrap_recordings(path):
    recs = []
    for filename in os.listdir("{0}/pictures".format(path)):
        ts = filename.split('.')[0]
        with open("{0}/outputs/{1}.json".format(path, ts), "r") as f:
            out = json.load(f)
        with open("{0}/distances/{1}.json".format(path, ts), "r") as f:
            dists = json.load(f)
        with open("{0}/pictures/{1}.jpg".format(path, ts), "rb") as img:
            pic_binary = base64.b64encode(img.read())
            pic_str = pic_binary.decode("utf-8")
        recs.append({"ts": ts, "pic": pic_str, "dist": dists, "out": out})
    return recs


while True:
    # Check if there is something in the directories
    if os.listdir("{0}/pictures".format(config.LOCAL_PATH_RECORDINGS)):

        # Collect complete the whole data and store it in a list
        data = wrap_recordings(config.LOCAL_PATH_RECORDINGS)

        token = auth_client(config.MSG_BROKER_BASE_URL, config.USER, config.PASSWORD)
        success = post_data(data, config.MSG_BROKER_BASE_URL, token)

        if success:
            remove_files(config.LOCAL_PATH_RECORDINGS, ["pictures", "distances", "outputs"])

    time.sleep(config.SENDER_SLEEP_TIME)


#############
# Idea, zip #
#############
# Maybe it is better to send all recordings directly as zip file
# This causes less work for the client on the rasperry
# I did not figure out how to json-serialize whole directories