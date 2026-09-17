
import os
os.environ["WBT_LINUX"] = "MUSL"
import whitebox
whitebox.download_wbt(linux_musl=True, reset=True)
wbt = whitebox.WhiteboxTools()

# # SetInput
folder_path_B_R = '/workspace/data/AllMapsInOneFolder/decompressed/geokeyed/B_R'
folder_path = '/workspace/data//AllMapsInOneFolder/decompressed/geokeyed/'


# # Create output folder
output_MedianB_R5_folder = os.path.join(folder_path, 'MedianB_R5')


# # Ensure output folder exist
os.makedirs(output_MedianB_R5_folder, exist_ok=True)


# # Iterate over the files in the folder

for file_name in os.listdir(folder_path_B_R):
    file_path_B_R = os.path.join(folder_path_B_R, file_name)
    #check if the file is a TIFF
    if file_name.endswith('.tif'):
        base_name = os.path.splitext(file_name)[0]   
        
    
        # Construct the output file path for the filter
        output_MedianB_R5 = os.path.join(output_MedianB_R5_folder, f"{base_name}.tif")
            
  
        # Run ThiteboxTools Medianfilter on red band
        wbt.median_filter(
            i=file_path_B_R, 
            output=output_MedianB_R5,
            filterx=5,
            filtery=5,
        )
                
    
        print(f"Processing completed for {file_name}")


