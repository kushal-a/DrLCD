from typing import Any, Callable, List, Optional, Tuple
from .machine import machineConnection, Machine
from .ui_common import Resolution
import click
import json

class Sensor:
    @property
    def directCommand(self) -> str:
        raise NotImplementedError("Base class")

    @property
    def index(self) -> int:
        raise NotImplementedError("Base class")

    def interpret(self, values: List[str]) -> Any:
        raise NotImplementedError("Base class")

class TSL2561(Sensor):
    @Sensor.directCommand.getter
    def directCommand(self) -> str:
        return "M5500"

    @Sensor.index.getter
    def index(self) -> int:
        return 0

    def interpret(self, data: str) -> Any:
        return float(data.replace("mW/cm^2", "").strip())

class AS7625(Sensor):
    @Sensor.directCommand.getter
    def directCommand(self) -> str:
        return "M5501"

    @Sensor.index.getter
    def index(self) -> int:
        return 1

    def interpret(self, values: List[str]) -> Any:
        raise NotImplementedError("TBA")


def getSensor(sensor: str) -> Sensor:
    """
    Given a sensor name, return command and function to interpret reading
    """
    try:
        return {
            "TSL2561": TSL2561(),
            "AS7625": AS7625()
        }[sensor]
    except KeyError:
        raise RuntimeError(f"Unknown sensor {sensor}") from None

@click.command()
@click.argument("output", type=click.Path())
@click.option("--port", type=str, default="/dev/ttyACM0",
    help="Port for device connection")
@click.option("--size", type=Resolution(),
    help="Screen size in millimeters")
@click.option("--resolution", type=Resolution(),
    help="Number of samples in vertical and horizontal direction")
@click.option("--sensor", type=click.Choice(["TSL2561", "AS7625"]), default="TSL2561",
    help="Sensor used for measurement")
@click.option("--feedrate", type=int, default=200,
    help="Feedrate for the measurement")
@click.option("--fast", is_flag=True,
    help="Use fast acquisition method")
def measureLcd(port, output, size, resolution, sensor, feedrate, fast) -> None:
    """
    Take and LCD measurement and save the result into a file
    """

    print("Start position:")
    print("__________________________________")
    print("     |                      |     ")
    print("     |                      |     ")
    print("     |                      |     ")
    print("     |                      |     ")
    print("     |                      |     ")
    print("     | X                    |     ")
    
    measurement = {
        "sensor": sensor,
        "size": size,
        "resolution": resolution
    }

    sensor = getSensor(sensor)

    with machineConnection(port) as machine:
        print("port done")
        machine.command("M17")
        print("M17 done")
        machine.command("G92 X0 Y0")
        print("G92 X0 Y0 done")
        machine.command(f"G0 X0 Y0 F{feedrate}")

        if fast:
            measurements = fastMeasurement(machine, size, resolution, sensor, feedrate)
        else:
            measurements = conservativeMeasurement(machine, size, resolution, sensor, feedrate)

        machine.command(f"G0 X0 Y0 F{feedrate}")
        machine.command("M400", timeout=40)
        machine.command("M18")
    measurement["measurements"] = measurements

    with open(output, "w") as f:
        json.dump(measurement, f)


def fastMeasurement(machine: Machine, size: Tuple[int, int],
        resolution: Tuple[int, int], sensor: Sensor, feedrate: int) -> List[List[Any]]:
    feedMultiplier = 1.0
    measurements = []
    for y in range(resolution[1]):
        targetY = (y + 0.5) * (size[1]/1.2) / (resolution[1])
        print(f"Row {y + 1} / {resolution[1]}, {targetY}")


        startX, targetX = 0, size[0]/1.2
        if y % 2 == 1:
            startX, targetX = targetX, startX

        while True:
            machine.command(f"G1 X{startX} Y{targetY} F{feedrate}")
            machine.command("M400")
            values = machine.command(f"M6000 S{resolution[0]} P{sensor.index} X{targetX} F{feedrate * feedMultiplier}")
            #print(values)
            if any("Missed" in x for x in values):  
                feedMultiplier *= 0.95
                print(f"Measurement unsuccessful, lowering feedrate to {feedrate * feedMultiplier}")
                continue
            # if len(values) != resolution[0]:
            #     print("Warning, some samples were missing; retrying")
            #     continue
            x = 0
            while True:
                if x<len(values):
                    if "mW/cm^2" not in values[x]:
                        values.pop(x)
                    else:
                        x=x+1
                else:
                    break
            break
        print(len(values))
        row = [sensor.interpret(x) for x in values]
        if y % 2 == 1:
           row = reversed(row)
        row = list(row)
        measurements.append(row)
        #print(f"  Got {measurements[-1]}")
        print("Got:")
        for i in range(len(row)):
            print(row[i])
    return measurements

def conservativeMeasurement(machine: Machine, size: Tuple[int, int],
        resolution: Tuple[int, int], sensor: Sensor, feedrate: int) -> List[List[Any]]:
    measurements = []
    for y in range(resolution[1]):
        row = [0 for x in range(resolution[0])]

        xRange = range(resolution[0])
        if y % 2 == 1:
            xRange = reversed(xRange)
        for x in xRange:
            targetX = x * (size[0]/1.2) / (resolution[0] - 1)
            targetY = y * (size[1]/1.2) / (resolution[1] - 1)
            command = f"G1 X{targetX} Y{targetY} F{feedrate}"
            machine.command(command)
            machine.command("M400", timeout=15)
            rawData = machine.command(sensor.directCommand)
            data = sensor.interpret(rawData[0])
            print(f"{x}, {y}: {data}")
            row[x] = data
        measurements.append(row)
    return measurements
