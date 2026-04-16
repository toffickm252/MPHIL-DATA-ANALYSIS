#  Based on BatchExportMTB by Trinoma SARL (GNU GPLv3)
#  Original: https://github.com/trinoma/BatchExportMTB
#  Customized to export only Accelerometer, Gyroscope, and Magnetometer data as CSV

from glob import glob
import os
import xsensdeviceapi as xda


def export_one_file(filename, output_dir=None) -> None:
    """Export one MTB file to a CSV file containing Acc, Gyr, and Mag data.

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

    # Get the device object
    device = control.device(control.deviceIds()[1])
    assert (device != 0)

    print("Device: %s, with ID: %s found in file" % (device.productCode(), device.deviceId().toXsString()))

    # Enable data retention so we can read packets back
    device.setOptions(xda.XSO_RetainBufferedData, xda.XSO_None)

    # Load the log file and wait until it is loaded
    print("Loading the file...")
    device.loadLogFile()
    device.waitForLoadLogFileDone()
    print("File is fully loaded")

    # Get total number of samples
    packetCount = device.getDataPacketCount()
    print(f"Total packets: {packetCount}")

    # CSV header
    header = "Acc_X,Acc_Y,Acc_Z,Gyr_X,Gyr_Y,Gyr_Z,Mag_X,Mag_Y,Mag_Z\n"

    # Export the data
    print("Exporting the data...")
    rows = []
    index = 0
    while index < packetCount:
        # Retrieve a packet
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

    # Build output file path
    base_name = os.path.splitext(os.path.basename(filename))[0]
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        export_path = os.path.join(output_dir, f"{base_name}.csv")
    else:
        export_path = f"{filename.split('.mtb')[0]}.csv"

    with open(export_path, "w") as outfile:
        outfile.write(header)
        outfile.write("\n".join(rows))
        outfile.write("\n")

    print(f"Exported {len(rows)} rows to: {export_path}")
    print()

    print("Closing XsControl object...")
    control.close()


if __name__ == '__main__':
    # ============================================================
    # CONFIGURE THESE TWO PATHS BEFORE RUNNING
    # ============================================================

    # Folder containing your .mtb files (searches subfolders too)
    data_dir = r"D:\Compressed\lavikinnean-data\10"

    # Folder where CSV files will be saved (set to None to save next to .mtb files)
    output_dir = r"D:\Compressed\lavikinnean-data\csv_output_10"

    # ============================================================

    all_mtb_files = glob(os.path.join(data_dir, "**", "*.mtb"), recursive=True)

    if not all_mtb_files:
        print(f"No .mtb files found in: {data_dir}")
        print("Please check the path and try again.")
    else:
        print(f"Found {len(all_mtb_files)} .mtb file(s) in: {data_dir}")
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