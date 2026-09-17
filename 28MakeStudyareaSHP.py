import os
import glob
from osgeo import gdal, ogr, osr
import numpy as np

def extract_boundary_to_shapefile(input_folder, output_shapefile):
    """
    Extract boundaries of all TIFF files in a folder to a single shapefile
    """
    
    # Get all TIFF files in the folder
    tiff_pattern = os.path.join(input_folder, "*.tif")
    tiff_files = glob.glob(tiff_pattern)
    
    print(f"Found {len(tiff_files)} TIFF files to process")
    
    if not tiff_files:
        print("No TIFF files found!")
        return
    
    # Create output shapefile
    driver = ogr.GetDriverByName("ESRI Shapefile")
    
    # Remove existing shapefile if it exists
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    
    # Create new shapefile
    datasource = driver.CreateDataSource(output_shapefile)
    
    # Create layer with polygon geometry
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3006)  # Assuming SWEREF99 TM
    layer = datasource.CreateLayer("boundaries", srs, ogr.wkbPolygon)
    
    # Add fields to store information about each file
    layer.CreateField(ogr.FieldDefn("filename", ogr.OFTString))
    layer.CreateField(ogr.FieldDefn("width", ogr.OFTInteger))
    layer.CreateField(ogr.FieldDefn("height", ogr.OFTInteger))
    layer.CreateField(ogr.FieldDefn("xmin", ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn("ymin", ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn("xmax", ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn("ymax", ogr.OFTReal))
    
    processed = 0
    failed = 0
    
    for tiff_file in tiff_files:
        try:
            # Open TIFF file
            dataset = gdal.Open(tiff_file)
            if not dataset:
                print(f"Failed to open: {os.path.basename(tiff_file)}")
                failed += 1
                continue
            
            # Get geotransform and calculate bounds
            geotransform = dataset.GetGeoTransform()
            width = dataset.RasterXSize
            height = dataset.RasterYSize
            
            # Calculate corner coordinates
            xmin = geotransform[0]
            ymax = geotransform[3]
            xmax = xmin + width * geotransform[1]
            ymin = ymax + height * geotransform[5]
            
            # Create polygon geometry for the boundary
            ring = ogr.Geometry(ogr.wkbLinearRing)
            ring.AddPoint(xmin, ymin)  # Bottom-left
            ring.AddPoint(xmax, ymin)  # Bottom-right
            ring.AddPoint(xmax, ymax)  # Top-right
            ring.AddPoint(xmin, ymax)  # Top-left
            ring.AddPoint(xmin, ymin)  # Close ring
            
            polygon = ogr.Geometry(ogr.wkbPolygon)
            polygon.AddGeometry(ring)
            
            # Create feature and set geometry
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetGeometry(polygon)
            
            # Set attributes
            filename = os.path.basename(tiff_file)
            feature.SetField("filename", filename)
            feature.SetField("width", width)
            feature.SetField("height", height)
            feature.SetField("xmin", xmin)
            feature.SetField("ymin", ymin)
            feature.SetField("xmax", xmax)
            feature.SetField("ymax", ymax)
            
            # Add feature to layer
            layer.CreateFeature(feature)
            
            # Clean up
            feature = None
            dataset = None
            
            processed += 1
            if processed % 100 == 0:
                print(f"Processed {processed} files...")
                
        except Exception as e:
            print(f"Error processing {os.path.basename(tiff_file)}: {e}")
            failed += 1
    
    # Clean up
    datasource = None
    
    print(f"\n=== Processing Complete ===")
    print(f"Successfully processed: {processed} files")
    print(f"Failed: {failed} files")
    print(f"Output shapefile: {output_shapefile}")
    
    return processed, failed

def main():
    # Set input and output paths
    input_folder = "/workspace/data/AllSwedishXGBoospredicedArableLanduseMaps"
    output_shapefile = "/workspace/data/map_boundaries.shp"
    
    print("=== TIFF Boundary Extraction ===")
    print(f"Input folder: {input_folder}")
    print(f"Output shapefile: {output_shapefile}")
    print("=" * 40)
    
    # Check if input folder exists
    if not os.path.exists(input_folder):
        print(f"Error: Input folder does not exist: {input_folder}")
        return
    
    # Extract boundaries
    processed, failed = extract_boundary_to_shapefile(input_folder, output_shapefile)
    
    if processed > 0:
        print(f"\n✓ Success! Created shapefile with {processed} polygon boundaries")
        print(f"You can now open {output_shapefile} in QGIS/ArcGIS to:")
        print("  - View the spatial distribution of your maps")
        print("  - Identify gaps where maps are missing")
        print("  - Check for overlaps or misalignments")
    else:
        print("✗ No boundaries were extracted")

if __name__ == "__main__":
    main()