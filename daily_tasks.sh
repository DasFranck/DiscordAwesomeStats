CONFIG_FILE=$1

./venv/bin/python ./getter.py $CONFIG_FILE
./venv/bin/python ./generate_message_count.py $CONFIG_FILE
./venv/bin/python ./notifier.py $CONFIG_FILE