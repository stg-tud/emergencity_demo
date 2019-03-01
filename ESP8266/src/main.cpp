#include <Arduino.h>
#include <ESP8266WiFi.h>

#include <CmdBuffer.hpp>
#include <CmdCallback.hpp>
#include <CmdParser.hpp>

#include <WifiEspNow.h>

#include "helpers.h"

// Helpers for parsing commands received via serial.
CmdParser cmd_parser;
CmdBuffer<WIFIESPNOW_MAXMSGLEN> cmd_buffer;

int peer_addr() {
    uint8_t my_mac[6];
    wifi_get_macaddr(SOFTAP_IF, my_mac);

    int i;
    for (i = 0; i <= 1; i++) {
        if (memcmp(nodes[i], my_mac, 6) != 0) {
            return i;
        }
    }

    return -1;
}

// Switch to crisis mode by downclocking the ESP..
void morph_crisis() {
    // Notify about switch and wait 100 ms for flush.
    Serial.print("Received CRISIS command. Morphing to crisis mode.\n");
    delay(100);

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
void print_log(const uint8_t mac[6], const uint8_t *buf, size_t count, void *cbarg) {
    if (strcasecmp(CRISIS_CMD, (const char *)buf) == 0) {
        morph_crisis();
    } else {
        Serial.printf("%s\n", (const char *)buf);
    }
}

void setup() {
    Serial.begin(115200);
    delay(100);

    Serial.print("Setting up Wi-Fi AP.\n");

    // Setting up Wi-Fi AP.
    WiFi.persistent(false);
    WiFi.mode(WIFI_AP);
    WiFi.softAP("emergenCITY", nullptr, 6);
    WiFi.softAPdisconnect(false);

    // Start the Wi-Fi. If it does not work, restart the device.
    bool ok = WifiEspNow.begin();
    if (!ok) {
        Serial.print("WifiEspNow.begin() failed. Rebooting.\n");
        ESP.restart();
    }

    // This is the callback for printing received data.
    WifiEspNow.onReceive(print_log, nullptr);

    // To be able to communicate, the two ESPs have add each other to the peers list.
    // Therefore, we first get the mac address, and check which of the two ESPs we have.
    ok = WifiEspNow.addPeer(nodes[peer_addr()]);
    if (!ok) {
        Serial.print("WifiEspNow.addPeer() failed. Rebooting.\n");
        ESP.restart();
    }
}

void loop() {
    // Timout after 3 seconds.
    if (!cmd_buffer.readFromSerial(&Serial, 3000)) {
        return;
    }

    // Received an error, most likely because empty string.
    if (cmd_parser.parseCmd(&cmd_buffer) == CMDPARSER_ERROR) {
        Serial.print("Got empty string.\n");
        return;
    }

    // Send the data received over Serial via Wi-Fi.
    WifiEspNow.send(nodes[peer_addr()], cmd_buffer.getBuffer(), WIFIESPNOW_MAXMSGLEN);

    // If we have received the "crisis" command, switch to crisis mode.
    if (cmd_parser.equalCommand(CRISIS_CMD)) {
        morph_crisis();
    }

    // Clear the buffer to get rid of remaining junk.
    cmd_buffer.clear();
}
