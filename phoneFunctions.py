import androidhelper as android
from urllib import request as urllib
import time
import getpass
import json
import base64

url = "http://10.200.208.148:5001/api/"
droid = android.Android()

def sendMessage(data, key):
    print("Message sent")
    droid.smsSend(data[0], data[1])

def sendUnreadMessages(args, key):
    print("Unread Messages Sent")
    messages = droid.smsGetMessages(True, "inbox").result
    data = base64.b64encode(json.dumps({"data":messages, "key":key}).encode("UTF-8")).decode("UTF-8").replace("/", "[")
    urllib.urlopen(url+"sendUnreadMessages/{0}/{1}".format(data, key))

def main():
    username = str(input("Username: "))
    password = getpass.getpass("Password: ")
    try:
        check = urllib.urlopen(url+"login/{0}/{1}".format(username, password)).read().decode("UTF-8")
    except:
        print("Web server may be down")
        time.sleep(10)
        main()
        return
    print (check)
    data = json.loads(check)
    if data['success']:
        key = data['key']
    else:
        print("Login Failed")
        main()
        return
    

    commands = {
            "sendMessage":sendMessage,
            "sendUnreadMessages":sendUnreadMessages,
    }

    while True:
        try:
            ping = json.loads(urllib.urlopen(url+"ping/{}".format(key)).read().decode("UTF-8"))
        except:
            print("Web server may be down")
            time.sleep(10)
            continue
        print (ping)
        if ping['data']:
            try:
                command = ping['data']['command']
                commands[command](ping['data']['args'], key)
            except:
                print("Malformed packet")
        time.sleep(2)

if __name__ == "__main__":
    main()
