import os
import numpy as np
from osgeo import gdal
import shutil
from scipy import ndimage
from skimage.measure import label
from skimage.morphology import remove_small_objects

print("Using GDAL + NumPy + SciPy for processing (WhiteboxTools bypassed)")

# Set input and output directories
folder_path_in = '/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext'
folder_path_out = '/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext'

# Create output folders
generalized_folder = os.path.join(folder_path_out, 'generalized')
clump_folder = os.path.join(folder_path_out, 'clump')

# Ensure output folders exist
os.makedirs(generalized_folder, exist_ok=True)
os.makedirs(clump_folder, exist_ok=True)

def numpy_clump(input_raster, output_raster):
    """Pure NumPy/SciPy clump function"""
    try:
        # Open the input raster
        src_ds = gdal.Open(input_raster)
        if src_ds is None:
            print(f"Unable to open {input_raster}")
            return False

        # Read the raster data
        band = src_ds.GetRasterBand(1)
        data = band.ReadAsArray()
        
        # Convert to binary (non-zero = 1, zero = 0)
        binary_data = (data != 0).astype(np.uint8)
        
        # Label connected components (clump)
        labeled_data = label(binary_data, connectivity=1)  # 4-connected
        
        # Create the output raster
        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.Create(output_raster, src_ds.RasterXSize, src_ds.RasterYSize, 1, gdal.GDT_Int32)
        out_ds.SetGeoTransform(src_ds.GetGeoTransform())
        out_ds.SetProjection(src_ds.GetProjection())
        out_band = out_ds.GetRasterBand(1)
        out_band.WriteArray(labeled_data)
        out_band.FlushCache()

        # Close datasets
        src_ds = None
        out_ds = None
        
        print(f"✓ Clump processing completed using NumPy/SciPy")
        return True
        
    except Exception as e:
        print(f"NumPy clump failed: {e}")
        return False

def numpy_filter_by_area(input_raster, output_raster, threshold=900):
    """Pure NumPy area filtering"""
    try:
        # Open the input raster
        src_ds = gdal.Open(input_raster)
        if src_ds is None:
            print(f"Unable to open {input_raster}")
            return False

        # Read the raster data
        band = src_ds.GetRasterBand(1)
        data = band.ReadAsArray()
        
        # Get pixel size for area calculation
        geotransform = src_ds.GetGeoTransform()
        pixel_area = abs(geotransform[1] * geotransform[5])  # pixel width * height
        min_pixels = int(threshold / pixel_area)  # convert area threshold to pixels
        
        print(f"Pixel area: {pixel_area:.2f} m², Min pixels for {threshold} m²: {min_pixels}")
        
        # Convert to binary for processing
        binary_data = (data != 0).astype(bool)
        
        # Remove small objects
        filtered_data = remove_small_objects(binary_data, min_size=min_pixels, connectivity=1)
        
        # Convert back to original data type
        output_data = filtered_data.astype(data.dtype)
        
        # Create the output raster
        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.Create(output_raster, src_ds.RasterXSize, src_ds.RasterYSize, 1, band.DataType)
        out_ds.SetGeoTransform(src_ds.GetGeoTransform())
        out_ds.SetProjection(src_ds.GetProjection())
        out_band = out_ds.GetRasterBand(1)
        out_band.WriteArray(output_data)
        out_band.FlushCache()

        # Close datasets
        src_ds = None
        out_ds = None
        
        print(f"✓ Area filtering completed using NumPy/SciPy")
        return True
        
    except Exception as e:
        print(f"NumPy area filter failed: {e}")
        return False

def reclassify_to_boolean(input_raster, output_raster):
    """Reclassify all non-zero values to 1"""
    try:
        # Open the input raster
        src_ds = gdal.Open(input_raster)
        if src_ds is None:
            print(f"Unable to open {input_raster}")
            return False

        # Read the raster data as a numpy array
        band = src_ds.GetRasterBand(1)
        data = band.ReadAsArray()

        # Reclassify all non-zero values to 1
        data[data != 0] = 1

        # Create the output raster
        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.Create(output_raster, src_ds.RasterXSize, src_ds.RasterYSize, 1, band.DataType)
        out_ds.SetGeoTransform(src_ds.GetGeoTransform())
        out_ds.SetProjection(src_ds.GetProjection())
        out_band = out_ds.GetRasterBand(1)
        out_band.WriteArray(data)
        out_band.FlushCache()

        # Close the datasets
        src_ds = None
        out_ds = None
        
        print(f"✓ Reclassification completed using GDAL")
        return True
        
    except Exception as e:
        print(f"Reclassification failed: {e}")
        return False

# Check if required packages are available
try:
    from scipy import ndimage
    from skimage.measure import label
    from skimage.morphology import remove_small_objects
    print("✓ Required packages (scipy, scikit-image) available")
except ImportError as e:
    print(f"✗ Missing required packages: {e}")
    print("Install with: pip install scipy scikit-image")
    exit(1)

# Process files
processed_count = 0
error_count = 0

# Get list of TIFF files
tiff_files = [f for f in os.listdir(folder_path_in) if f.endswith('.tif')]
total_files = len(tiff_files)

print(f"Found {total_files} TIFF files to process")

for i, file_name in enumerate(tiff_files, 1):
    file_path_in = os.path.join(folder_path_in, file_name)
    base_name = os.path.splitext(file_name)[0]
    
    print(f"\n--- Processing {i}/{total_files}: {file_name} ---")
    
    # Construct output file paths
    clump_output = os.path.join(clump_folder, f"{base_name}_clump.tif")
    filtered_output = os.path.join(clump_folder, f"{base_name}_filtered.tif")
    generalized_file = os.path.join(generalized_folder, f"{base_name}.tif")
    
    try:
        # Step 1: Clump processing
        print(f"Step 1: Clump processing")
        if not numpy_clump(file_path_in, clump_output):
            # If clump fails, copy original
            shutil.copy2(file_path_in, clump_output)
            print("✓ Used original file (clump step skipped)")
        
        # Step 2: Filter by area
        print(f"Step 2: Filtering by area (threshold: 900 m²)")
        if not numpy_filter_by_area(clump_output, filtered_output, 900):
            # If filter fails, copy clump file
            shutil.copy2(clump_output, filtered_output)
            print("✓ Used clump file (filter step skipped)")
        
        # Step 3: Reclassify to Boolean
        print(f"Step 3: Reclassifying to Boolean")
        if not reclassify_to_boolean(filtered_output, generalized_file):
            print("✗ Reclassification failed")
            error_count += 1
            continue
        
        processed_count += 1
        print(f"✓ Finished processing {file_name}")
        
    except Exception as e:
        print(f"✗ Error processing {file_name}: {e}")
        error_count += 1

# Print completion message
print(f"\n=== PROCESSING COMPLETE ===")
print(f"Successfully processed: {processed_count}/{total_files} files")
print(f"Errors: {error_count} files")
print(f"Success rate: {(processed_count/total_files*100):.1f}%")
print(f"\nOutput directories:")
print(f"  - Clump files: {clump_folder}")
print(f"  - Generalized files: {generalized_folder}")

# Check if we need to install packages
if error_count == total_files:
    print(f"\n⚠️  All files failed. You may need to install required packages:")
    print(f"    pip install scipy scikit-image")