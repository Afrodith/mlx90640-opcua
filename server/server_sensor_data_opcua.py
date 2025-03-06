import asyncio
import board
import busio
import adafruit_mlx90640
import numpy as np
from asyncua import Server, ua


async def read_thermal_data(mlx, thermal_node):
    """ Reads MLX90640 data and updates OPC UA node at 32Hz """
    frame = [0] * 768  # 32x24 pixels

    while True:
        try:
            mlx.getFrame(frame)  # Capture frame from sensor
            thermal_array = np.array(frame, dtype=np.float32)

            # Update OPC UA node
            await thermal_node.write_value(
                ua.Variant(thermal_array.tolist(), ua.VariantType.Double)
            )
            print("Updated OPC UA node with new thermal data")

            await asyncio.sleep(1 / 32)  # Maintain 32Hz refresh rate
        except Exception as e:
            print("Error reading sensor:", e)
            await asyncio.sleep(1)  # Avoid tight error loops


async def main():
    # Initialize I2C and MLX90640
    i2c = busio.I2C(board.SCL, board.SDA,frequency=400000)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
    frame = [0] * 768  # 32x24 pixels

    # Create OPC UA Server
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("BeagleBone Thermal Server")

    # Initialize the server address space (creates namespace array and nodes)
    await server.init()

    # Now register a custom namespace
    ns_idx = await server.register_namespace("BeagleBoneThermal")

    # Get the Objects node
    objects = server.nodes.objects

    # Create a Variable Node for thermal data (as a flat array)
    thermal_node = await objects.add_variable(
        ns_idx,
        "ThermalData",
        ua.Variant([0.0] * 768, ua.VariantType.Double)
    )
    # Make the node writable so it can be updated
    await thermal_node.set_writable()

    async with server:
            await asyncio.gather(
                read_thermal_data(mlx, thermal_node)
            )

if __name__ == "__main__":
    asyncio.run(main())
