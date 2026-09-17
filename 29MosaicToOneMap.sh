#!/bin/bash
# Mosaic 4 Swedish Arable Land Maps with MAX merge (1 overwrites 0)
# Script: MosaicToOneMap.sh

echo "=========================================="
echo "Mosaicking 4 Swedish Arable Land Maps"
echo "Using MAX algorithm (1 overwrites 0)"
echo "=========================================="

# Set base directory
BASE_DIR="/workspace/data/Mosaics"

# Define input files from subfolders
INPUT1="$BASE_DIR/North/LandUseNoGraphicsNorth.tif"
INPUT2="$BASE_DIR/MidNorth/LandUseNoGraphicsMidNorth.tif"
INPUT3="$BASE_DIR/MidSouth/LandUseNoGraphicsMidSouth.tif"
INPUT4="$BASE_DIR/South/LandUseNoGraphicsSouth.tif"

# Define output file
OUTPUT="$BASE_DIR/ArableLandEconomicMaps.tif"

# Temporary VRT file
TEMP_VRT="$BASE_DIR/temp_mosaic.vrt"

echo "Checking input files..."

# Check if all input files exist
for file in "$INPUT1" "$INPUT2" "$INPUT3" "$INPUT4"; do
    if [ -f "$file" ]; then
        echo "✓ Found: $(basename "$file")"
    else
        echo "✗ Missing: $file"
        exit 1
    fi
done

echo ""
echo "Creating mosaic with MAX algorithm (1 overwrites 0)..."

# Step 1: Create VRT file with MAX merge algorithm
echo "Step 1: Building VRT with MAX merge algorithm..."
gdalbuildvrt -overwrite "$TEMP_VRT" "$INPUT1" "$INPUT2" "$INPUT3" "$INPUT4"

if [ $? -eq 0 ]; then
    echo "✓ VRT created successfully"
else
    echo "✗ Failed to create VRT"
    exit 1
fi

# Step 2: Convert VRT to final TIFF using MAX algorithm
echo "Step 2: Converting VRT to final TIFF with MAX merge..."
gdal_calc.py \
    -A "$INPUT1" \
    -B "$INPUT2" \
    -C "$INPUT3" \
    -D "$INPUT4" \
    --outfile="$OUTPUT" \
    --calc="maximum(maximum(maximum(A,B),C),D)" \
    --co="COMPRESS=LZW" \
    --co="PREDICTOR=2" \
    --co="TILED=YES" \
    --co="BLOCKXSIZE=512" \
    --co="BLOCKYSIZE=512" \
    --type=Byte \
    --overwrite

if [ $? -eq 0 ]; then
    echo "✓ Final mosaic created successfully with MAX merge"
else
    echo "✗ Failed to create final mosaic"
    exit 1
fi

# Step 3: Clean up temporary VRT
echo "Step 3: Cleaning up temporary files..."
rm -f "$TEMP_VRT"

# Display results
echo ""
echo "=========================================="
echo "Mosaic Creation Complete!"
echo "=========================================="
echo "Output file: $OUTPUT"
echo "Merge method: MAX (1 overwrites 0)"

# Get file info
if [ -f "$OUTPUT" ]; then
    echo "File size: $(ls -lh "$OUTPUT" | awk '{print $5}')"
    echo ""
    echo "Checking unique values in output:"
    gdalinfo -stats "$OUTPUT" | grep -E "(Minimum|Maximum|Mean)"
else
    echo "✗ Output file not found!"
    exit 1
fi

echo ""
echo "Mosaic script completed successfully!"
echo "Result: Complete Sweden map with arable land (1) and non-arable (0)"