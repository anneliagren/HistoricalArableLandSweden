
# Set the pathsNorth
output_folder="/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext/generalized/North"


# Create a VRT file from all TIFFs in the subfolder
gdalbuildvrt "$output_folder/composite.vrt" "$output_folder"/*.tif

# Convert the VRT file to a GeoTIFF
gdal_translate -ot Byte "$output_folder/composite.vrt" "$output_folder/LandUseNoGraphicsNorth.tif"



# Set the pathsMidNorth
output_folder="/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext/generalized/MidNorth"

# Create a VRT file from all TIFFs in the subfolder
gdalbuildvrt "$output_folder/composite.vrt" "$output_folder"/*.tif

# Convert the VRT file to a GeoTIFF
gdal_translate -ot Byte "$output_folder/composite.vrt" "$output_folder/LandUseNoGraphicsMidNorth.tif"



# Set the pathsMidSouth
output_folder="/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext/generalized/MidSouth"

# Create a VRT file from all TIFFs in the subfolder
gdalbuildvrt "$output_folder/composite.vrt" "$output_folder"/*.tif

# Convert the VRT file to a GeoTIFF
gdal_translate -ot Byte "$output_folder/composite.vrt" "$output_folder/LandUseNoGraphicsMidSouth.tif"


# Set the pathsSouth
output_folder="/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps/Notext/generalized/South"

# Create a VRT file from all TIFFs in the subfolder
gdalbuildvrt "$output_folder/composite.vrt" "$output_folder"/*.tif

# Convert the VRT file to a GeoTIFF
gdal_translate -ot Byte "$output_folder/composite.vrt" "$output_folder/LandUseNoGraphicsSouth.tif"
