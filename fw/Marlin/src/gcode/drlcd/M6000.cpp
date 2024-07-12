#include "../../feature/drlcd/drlcd.h"
#include "../gcode.h"


#include <src/module/planner.h>
#include <src/module/motion.h>
#include <src/gcode/parser.h>

void reportMeasurementMiss() {
    SERIAL_ECHO("Missed\n");
}

void GcodeSuite::M6000() {
    planner.synchronize();

    xy_pos_t startPoint = current_position;

    get_destination_from_command();
    int samples = parser.intval('S');
    int sensor = parser.intval('P');

    xy_pos_t direction = destination - startPoint;
    float length = direction.magnitude();
    float step = length / samples;
    float half_step = step / 2.0f;
    float step_inv = 1.0f / step;

    // We start the movement and wait for it to finish:
    prepare_line_to_destination();

    int lastMeasurement = 0;
    while (lastMeasurement < samples) {
        idle();
        get_cartesian_from_steppers();
        xy_pos_t current = cartes;
        float progress = (current - startPoint).magnitude();
        int measurementNo = (progress + half_step) * step_inv;
        int measurementAdv = measurementNo - lastMeasurement;
        if (measurementAdv > 1) {
            for (int i = 0; i != measurementAdv; i++)
                reportMeasurementMiss();
        } else if (measurementAdv == 1) {
            DR_LCD.measure_lux();
        }
        lastMeasurement = measurementNo;
    }

    planner.synchronize();
}
