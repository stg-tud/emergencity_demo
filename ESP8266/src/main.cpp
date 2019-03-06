#include "ESP8266WiFi.h"
#include <CmdBuffer.hpp>
#include <CmdCallback.hpp>
#include <CmdParser.hpp>
#include <ESPAsyncTCP.h>

#include "helpers.h"

// default MSS is 536 byte
#define MAX_LEN 536

#define SERVER_PORT 8080
const char *ssid = "emergenCITY MC Management";
const char *password = "emergenCITY MC Management";

// Helpers for parsing commands received via serial.
CmdParser cmd_parser;
CmdBuffer<MAX_LEN> cmd_buffer;

AsyncClient *client;
static std::vector<AsyncClient *> clients;

bool isServer() {
    return WiFi.macAddress().startsWith("DC:4F:22:18:2F:B0"); // DC:4F:22:18:2F:B0 is the Server
}

void morph_crisis() {
    // Notify about switch and wait for flush.
    Serial.print("[!] Received CRISIS command. Morphing to crisis mode.\n");
    Serial.flush();

    // This is the actual downclocking.
    // We have to wait 100 ms until the ESP is back functional
    write_register(103, 4, 1, 0x48);
    write_register(103, 4, 2, 0xf1);
    delay(100);

    // Since we downclocked everything, the baud rate also changes.
    // The serial monitor, however, still wants 115200, so we have to
    // speed up the ESP baud rate by 115200 / 13.5 * 32
    // Again, wait 100 ms for the ESP to be back functional.
    Serial.begin(273067);
    delay(100);
}

// This prints the received data on the receiver.
// If "crisis" is received, morph to crisis mode.
void cmp_recv(uint8_t *buf, size_t count) {
    //buffer is not \0 terminated
    buf[count] = (uint8_t)'\0';

    if (strcasecmp(CRISIS_CMD, (const char *)buf) == 0) {
        morph_crisis();
    } else if ((strcasecmp(RESTART_CMD, (const char *)buf) == 0)){
        ESP.restart();
    } else {
        Serial.printf("%s\n", (const char *)buf);
    }
}

/*
 *
 * CLIENT FUNCTIONS
 *
 */

static void send_to_server(String message) {
    while (!client->canSend()) {
        Serial.println("Can not send...");
        delay(5);
    }

	if (client->space() > message.length() && client->canSend()) {
        const char * a = message.c_str();
		client->add(a, strlen(a));
		client->send();
	}
}

/* event callbacks */
static void client_handleData(void* arg, AsyncClient* client, void *data, size_t len) {
    cmp_recv((uint8_t*)data, len);
}

void client_onConnect(void* arg, AsyncClient* client) {
}


void client_setup() {
	// connects to access point
	WiFi.mode(WIFI_STA);
	WiFi.begin(ssid, password);

	while (WiFi.status() != WL_CONNECTED) {
		delay(500);
	}

    Serial.println("[!] connected to Server");

	client = new AsyncClient;
	client->onData(&client_handleData, client);
	client->onConnect(&client_onConnect, client);
	client->connect(WiFi.gatewayIP(), SERVER_PORT);
}

/*
 *
 * SERVER FUNCTIONS
 *
 */

 /* clients events */
static void handleError(void* arg, AsyncClient* client, int8_t error) {
	Serial.printf("[!] connection error %s from client %s\n", client->errorToString(error), client->remoteIP().toString().c_str());
}

static void handleData(void* arg, AsyncClient* client, void *data, size_t len) {
    cmp_recv((uint8*)data,len);
}

static void send_to_all_clients(String message) {
    for (std::vector<int>::size_type i = 0; i < clients.size(); i++) {
        AsyncClient *client = clients[i];
        const char * a = message.c_str();


        while (!client->canSend()) {
            Serial.println("Can not send...");
            delay(5);
        }

        if (client->space() > strlen(a) && client->canSend()) {
            client->add(a, strlen(a));
            client->send();
        }
    }
}

static void handleDisconnect(void* arg, AsyncClient* client) {
	Serial.printf("[!] client %s disconnected \n", client->remoteIP().toString().c_str());
}

static void handleTimeOut(void* arg, AsyncClient* client, uint32_t time) {
	Serial.printf("[!] client ACK timeout ip: %s \n", client->remoteIP().toString().c_str());
}

static void handleNewClient(void* arg, AsyncClient* client) {
	Serial.printf("[!] new client has been connected to server, ip: %s\n", client->remoteIP().toString().c_str());

	// add to list
	clients.push_back(client);

	// register events
	client->onData(&handleData, NULL);
	client->onError(&handleError, NULL);
	client->onDisconnect(&handleDisconnect, NULL);
	client->onTimeout(&handleTimeOut, NULL);
}

void server_setup() {
	// create access point
	while (!WiFi.softAP(ssid, password, 6, false, 15)) {
		delay(500);
	}

	AsyncServer* server = new AsyncServer(SERVER_PORT);
	server->onClient(&handleNewClient, server);
	server->begin();
}

/*
 *
 * MAIN FUNCTIONS
 *
 */

void setup() {
    Serial.begin(115200);
    delay(1000);

    if (isServer()) {
        server_setup();
    } else {
        client_setup();
    }

    Serial.flush();
    Serial.clearWriteError();
    cmd_buffer.clear();
}

void loop() {
    if (!cmd_buffer.readFromSerial(&Serial, 3000)) {
        return;
    }

    // Received an error, most likely because empty string.
    if (cmd_parser.parseCmd(&cmd_buffer) == CMDPARSER_ERROR) {
        Serial.print("Got empty string.\n");
        return;
    }

    // Send the data received over Serial via Wi-Fi.
    // Since we know our Serial-Input is textbased (nonbinary) we know it can be
    // interpreted as a String
    if (isServer()) {
        send_to_all_clients(cmd_buffer.getStringFromBuffer());
    } else {
        send_to_server(cmd_buffer.getStringFromBuffer());
    }

    // If we have received the "crisis" command, switch to crisis mode.
    if (cmd_parser.equalCommand(CRISIS_CMD)) {
        delay(500);
        morph_crisis();
    }

    if (cmd_parser.equalCommand(RESTART_CMD)) {
        delay(500);
        ESP.restart();
    }

    // Clear the buffer to get rid of remaining junk.
    cmd_buffer.clear();
}
