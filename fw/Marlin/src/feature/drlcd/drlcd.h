#include "../../inc/MarlinConfig.h"
#include "../../module/temperature.h"

class DR_lcd{
    public:
        void measure_lux(){
            int a = (int) thermalManager.temp_bed.celsius;
            SERIAL_ECHO(a);
            SERIAL_ECHO("mW/cm^2 \n");
        }

}

extern DR_LCD;