connect serial com6
cp samples\\esp8266\\boot.py /pyboard/boot.py
cp samples\\esp8266\\main.py /pyboard/main.py
rsync scpidev/ /pyboard/lib/scpidev
repl