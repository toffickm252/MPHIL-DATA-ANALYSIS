#  Based on BatchExportMTB by Trinoma SARL (GNU GPLv3)
#  Original: https://github.com/trinoma/BatchExportMTB
#  Customized to export only Accelerometer, Gyroscope, and Magnetometer data as CSV
#  Filtered to only export data from sensors of interest

from glob import glob
import os
import xsensdeviceapi as xda


# ============================================================
# SENSOR CONFIGURATION
# Maps sensor IDs to body location names
# Only sensors listed here will be exported
# ============================================================
SENSORS_OF_INTEREST = {
    "00B42DA3": "pelvis",
    "00B42D53": "left_tibia",
    "00B42DAE": "right_tibia",
}


def export_one_file(filename, output_dir=None) -> None:
    """Export one MTB file to CSV files for each sensor of interest.

    Args:
        filename (str): path to the MTB file to be exported
        output_dir (str): optional output directory for CSV files

    Returns:
        None
    """
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

    # Get all device IDs in this file
    device_ids = control.deviceIds()
    print(f"Found {len(device_ids)} device(s) in file")

    # Loop through all devices and export only sensors of interest
    for i in range(len(device_ids)):
        device = control.device(device_ids[i])
        if device == 0:
            continue

        sensor_id = device.deviceId().toXsString()
        product_code = device.productCode()

        # Check if this sensor is one we care about
        matched_location = None
        for sid, location in SENSORS_OF_INTEREST.items():
            if sensor_id.endswith(sid) or sid in sensor_id:
                matched_location = location
                break

        if matched_location is None:
            print(f"  Skipping sensor {sensor_id} ({product_code}) - not in sensors of interest")
            continue

        print(f"  Exporting sensor {sensor_id} ({product_code}) -> {matched_location}")

        # Enable data retention so we can read packets back
        device.setOptions(xda.XSO_RetainBufferedData, xda.XSO_None)

        # Load the log file and wait until it is loaded
        device.loadLogFile()
        device.waitForLoadLogFileDone()

        # Get total number of samples
        packetCount = device.getDataPacketCount()
        print(f"    Total packets: {packetCount}")

        # CSV header
        header = "Acc_X,Acc_Y,Acc_Z,Gyr_X,Gyr_Y,Gyr_Z,Mag_X,Mag_Y,Mag_Z\n"

        # Export the data
        rows = []
        index = 0
        while index < packetCount:
            packet = device.getDataPacketByIndex(index)

            if packet.containsCalibratedData():
                acc = packet.calibratedAcceleration()
                gyr = packet.calibratedGyroscopeData()
                mag = packet.calibratedMagneticField()

                row = (
                    f"{acc[0]:.6f},{acc[1]:.6f},{acc[2]:.6f},"
                    f"{gyr[0]:.6f},{gyr[1]:.6f},{gyr[2]:.6f},"
                    f"{mag[0]:.6f},{mag[1]:.6f},{mag[2]:.6f}"
                )
                rows.append(row)

            index += 1

        # Build output file path with sensor location in the name
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
    # ============================================================
    # CONFIGURE THESE TWO PATHS BEFORE RUNNING
    # ============================================================

    # Folder containing your .mtb files (searches subfolders too)
    data_dir = r"D:\Compressed\lavikinnean-data\03"

    # Folder where CSV files will be saved (set to None to save next to .mtb files)
    output_dir = r"D:\Compressed\lavikinnean-data\csv_output_03"

    # ============================================================

    all_mtb_files = glob(os.path.join(data_dir, "**", "*.mtb"), recursive=True)

    if not all_mtb_files:
        print(f"No .mtb files found in: {data_dir}")
        print("Please check the path and try again.")
    else:
        print(f"Found {len(all_mtb_files)} .mtb file(s) in: {data_dir}")
        print(f"Exporting only: {', '.join(SENSORS_OF_INTEREST.values())}")
        print()
        for file in all_mtb_files:
            try:
                export_one_file(file, output_dir)
            except Exception as e:
                print(f"ERROR processing {file}: {e}")
                print("Skipping this file and continuing...")
                print()

    print("=" * 60)
    print("Batch export complete!")
    print("=" * 60)