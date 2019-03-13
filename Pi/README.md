# emergenCITY Demonstrator Test Setup

## Dependencies

`docker`, `docker-compose`, `mosquitto` and a lot more for the python stuff.

## Running Mosquitto/Node Red

```
docker-compose up [-d]
```

**DEV MODE**
For development mode edit `docker-compose.yml` and comment out the USB device entry. Also use the `dummyEvents.py` event generator.

All sensor values are published using the python skripts (see below).
Only if the emergency state needs to be changed, use the following commands:

```
mosquitto_pub -h localhost -t city/alert_state -m "emergency"
```

```
mosquitto_pub -h localhost -t city/alert_state -m "love, peace and harmony"
```

Show dashboard UI:
http://[PI_IP]:1880/ui

Show node red editor:
http://[PI_IP]:1880


## Running the sensors
Start the `main.py` skript and everything should be up and runnning.

**DEVMODE**
If not on the real system use `dummyEvents.py` to generate randomized dummy events.
