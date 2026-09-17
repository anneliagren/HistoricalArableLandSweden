import os
import subprocess
import json

# Set input folder path
folder_path = '/workspace/data/AllMapsInOneFolder/decompressed/'

# Set output folder path
output_folder_path = '/workspace/data/AllMapsInOneFolder/decompressed/geokeyed'

# Create the output directory if it doesn't exist
os.makedirs(output_folder_path, exist_ok=True)

# Coordinate system to add (RT90 2.5 gon V)
coordinate_system = 'EPSG:3021'

def get_geotransform(file_path):
    """Get the geotransform information from a TIFF file using gdalinfo."""
    result = subprocess.run(['gdalinfo', '-json', file_path], capture_output=True, text=True, check=True)
    info = json.loads(result.stdout)
    geotransform = info['geoTransform']
    ulx = geotransform[0]
    uly = geotransform[3]
    lrx = ulx + geotransform[1] * info['size'][0]
    lry = uly + geotransform[5] * info['size'][1]
    return ulx, uly, lrx, lry

# List to store files that couldn't be processed
failed_files = []

# Iterate over the files in the folder
for file_name in os.listdir(folder_path):
    file_path = os.path.join(folder_path, file_name)
    
    # Check if the file is a TIFF
    if file_name.endswith('.tif'):
        base_name = os.path.splitext(file_name)[0]
        output_file = os.path.join(output_folder_path, f"{base_name}.tif")

        try:
            print(f"Processing {file_name}...")
            # Get geotransform information
            ulx, uly, lrx, lry = get_geotransform(file_path)
            print(f"Geotransform for {file_name}: ulx={ulx}, uly={uly}, lrx={lrx}, lry={lry}")
            
            # Run gdal_translate to add geokeys and correct georeferencing
            subprocess.run([
                'gdal_translate',
                '-a_srs', coordinate_system,
                '-a_ullr', str(ulx), str(uly), str(lrx), str(lry),
                file_path,
                output_file
            ], check=True)
            print(f"Geokeys and georeferencing added to {file_name}, saved as {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to process {file_name}: {e}")
            failed_files.append(file_name)
        except KeyError as e:
            print(f"Failed to process {file_name}: {e}")
            failed_files.append(file_name)

# Save the list of failed files
with open('failed_files.txt', 'w') as f:
    for file_name in failed_files:
        f.write(f"{file_name}\n")

print("Processing complete. Failed files have been saved to failed_files.txt.")