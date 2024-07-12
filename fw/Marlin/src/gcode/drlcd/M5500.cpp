#include "../../feature/drlcd/drlcd.h"
#include "../gcode.h"

void GcodeSuite::M5500() {
    DR_LCD.measure_lux();
}
