#include "../gcode.h"
#include <src/feature/drlcd/drlcd.h>

void GcodeSuite::M5500() {
    float value = DR_LCD.readTSL2561();
    SERIAL_ECHOPGM("Data: ", value);
    SERIAL_ECHO("\n");
}

void GcodeSuite::M5501() {
    auto values = DR_LCD.readAS7341();
    SERIAL_ECHO("Data: ");
    for (auto value : values) {
        SERIAL_ECHOPGM(" ", float(value));
    }
    SERIAL_ECHO("\n");
}

void GcodeSuite::M5502() {
    float value = DR_LCD.readML8511();
    SERIAL_ECHOPGM("Data: ", value);
    SERIAL_ECHO("\n");
}
