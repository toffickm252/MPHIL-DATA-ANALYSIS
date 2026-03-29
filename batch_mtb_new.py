#  Based on BatchExportMTB by Trinoma SARL (GNU GPLv3)
#  Original: https://github.com/trinoma/BatchExportMTB
#  Customized to export Accelerometer, Gyroscope, and Magnetometer data as CSV
#  Exports all 7 sensors

from glob import glob
import os
import xsensdeviceapi as xda


# ============================================================
# SENSOR CONFIGURATION
# Maps sensor IDs to body location names
# All 7 sensors will be exported
# ============================================================
SENSORS_OF_INTEREST = {
    "00B42DA3": "Pelvis",
    "00B42DA2": "right_femur",
    "00B42D4D": "left_femur",
    "00B42DAE": "right_tibia",
    "00B42D53": "left_tibia",
    "00B42D48": "right_foot",
    "00B42D4E": "left_foot",
}

# ============================================================
# CONFIGURE THESE TWO PATHS BEFORE RUNNING
# ============================================================
# Folder containing .mtb files (point directly at participant folder)
ROOT_DATA_DIR = r"D:\Compressed\lavikinnean-data\IMU_DATA\51"

# Folder where CSV files will be saved
ROOT_OUTPUT_DIR = r"D:\Compressed\lavikinnean-data\IMU_DATA\51_extracted"
# ============================================================


def export_one_file(filename, output_dir=None) -> None:
    print("=" * 60)
    print(f"Processing: {filename}")
    print("=" * 60)

    print("Creating XsControl object...")
    control = xda.XsControl_construct()
    assert (control != 0)

    xdaVersion = xda.XsVersion()
    xda.xdaVersion(xdaVersion)
    print("Using XDA version %s" % xdaVersion.toXsString())

    print("Opening log file...")
    if not control.openLogFile(filename):
        raise RuntimeError("Failed to open log file. Aborting.")
    print("Opened log file: %s" % filename)

    device_ids = control.deviceIds()
    print(f"Found {len(device_ids)} device(s) in file")

    matched_devices = []
    for i in range(len(device_ids)):
        device = control.device(device_ids[i])
        if device == 0:
            continue

        sensor_id = device.deviceId().toXsString()
        product_code = device.productCode()

        matched_location = None
        for sid, location in SENSORS_OF_INTEREST.items():
            if sensor_id.endswith(sid) or sid in sensor_id:
                matched_location = location
                break

        if matched_location is None:
            print(f"  Skipping sensor {sensor_id} ({product_code}) - not in sensors of interest")
            continue

        print(f"  Found sensor {sensor_id} ({product_code}) -> {matched_location}")
        device.setOptions(xda.XSO_RetainBufferedData, xda.XSO_None)
        matched_devices.append((device, matched_location))

    print("Loading log file for all sensors...")
    for device, location in matched_devices:
        device.loadLogFile()

    for device, location in matched_devices:
        device.waitForLoadLogFileDone()
    print("All sensors loaded")

    for device, matched_location in matched_devices:
        packetCount = device.getDataPacketCount()
        print(f"  Exporting {matched_location}: {packetCount} packets")

        header = "PacketCounter,Acc_X,Acc_Y,Acc_Z,Gyr_X,Gyr_Y,Gyr_Z,Mag_X,Mag_Y,Mag_Z\n"

        rows = []
        index = 0
        packet_counter = 0
        while index < packetCount:
            packet = device.getDataPacketByIndex(index)

            if packet.containsCalibratedData():
                acc = packet.calibratedAcceleration()
                gyr = packet.calibratedGyroscopeData()
                mag = packet.calibratedMagneticField()

                row = (
                    f"{packet_counter:05d},"
                    f"{acc[0]:.6f},{acc[1]:.6f},{acc[2]:.6f},"
                    f"{gyr[0]:.6f},{gyr[1]:.6f},{gyr[2]:.6f},"
                    f"{mag[0]:.6f},{mag[1]:.6f},{mag[2]:.6f}"
                )
                rows.append(row)
                packet_counter += 1

            index += 1

        base_name = os.path.splitext(os.path.basename(filename))[0]
        csv_filename = f"{base_name}_{matched_location}.csv"

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            export_path = os.path.join(output_dir, csv_filename)
        else:
            export_path = os.path.join(os.path.dirname(filename), csv_filename)

        with open(export_path, "w") as outfile:
            outfile.write(header)
            outfile.write("\n".join(rows))
            outfile.write("\n")

        print(f"    Exported {len(rows)} rows to: {export_path}")

    print()
    print("Closing XsControl object...")
    control.close()


if __name__ == '__main__':
    # Find all .mtb files in ROOT_DATA_DIR
    mtb_files = glob(os.path.join(ROOT_DATA_DIR, "*.mtb"))

    if not mtb_files:
        print(f"No .mtb files found in: {ROOT_DATA_DIR}")
    else:
        print(f"Found {len(mtb_files)} .mtb file(s) in: {ROOT_DATA_DIR}")
        print(f"Exporting sensors: {', '.join(SENSORS_OF_INTEREST.values())}")
        print()

        total_files = 0
        total_errors = 0

        for file in sorted(mtb_files):
            try:
                export_one_file(file, ROOT_OUTPUT_DIR)
                total_files += 1
            except Exception as e:
                print(f"ERROR processing {file}: {e}")
                print("Skipping this file and continuing...")
                total_errors += 1

        print()
        print("=" * 60)
        print("Batch export complete!")
        print(f"Processed: {total_files} files")
        print(f"Errors: {total_errors}")
        print(f"Output: {ROOT_OUTPUT_DIR}")
        print("=" * 60)