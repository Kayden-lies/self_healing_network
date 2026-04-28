import datetime

def log_event(logs, message):
    time = datetime.datetime.now().strftime("%H:%M:%S")
    logs.insert(0, f"[{time}] {message}")