import json

def handle(data):
    data = json.loads(data)
    i = 0
    if 'loop' in data:
        try:
            while True:
                i += 1
        except:
            pass
    user_answer = data["user_answer"]
    value_01 = data["value_01"]
    if data["value_02"]:

        if user_answer and value_01:
            user_answer = int(data["user_answer"])
            value_01 = int(data["value_01"])
            value_02 = int(data["value_02"])
            strg = data["strg"]

            if strg == "s":
                if user_answer < value_01 or user_answer==value_01:
                   status = -1
                if value_01 < user_answer < value_02:
                    status = 0
                if user_answer > value_02 or user_answer==value_02:
                    status = 1

            else:

                if user_answer <= value_01:
                    status = -1
                if value_01 <= user_answer <= value_02:
                    status = 0
                if user_answer > value_02:
                    status = 1
        else:
            status = 2
        status = json.dumps({"status": status})
    else:
        if user_answer and value_01:
            user_answer = int(data["user_answer"])
            value_01 = int(data["value_01"])

            if user_answer < value_01:
                status = -1
            if user_answer > value_01:
                status = 1
            if user_answer == value_01:
                status = 0
        else:
            status = 2

        status = json.dumps({"status": status})

    return status

