scp -r -P22222 custom_components/iot-data/ root@192.168.99.10:/mnt/data/supervisor/homeassistant/custom_components/
ssh -p22222 root@192.168.99.10 docker restart homeassistant
