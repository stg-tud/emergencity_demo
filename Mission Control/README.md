# emergenCITY Demonstrator Test Setup

## Dependencies

`docker`, `docker-compose` and `mosquitto`

### Linux

`sudo apt-get install mosquitto mosquitto-clients`

### Mac

`brew install mosquitto`

## Running the system

`docker-compose up`

```
mosquitto_pub -h localhost -t city/alert_state -m "emergency"
```

```
mosquitto_pub -h localhost -t city/alert_state -m "love, peace and harmony"
```

Port for mqtt: *1883*
Port for websockets: *9001*

Show dashboard UI:
http://localhost:1880/ui

Show node red editor:
http://localhost:1880
