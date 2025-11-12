import kagglehub

# Download latest version
path = kagglehub.dataset_download("trainingdatapro/cars-video-object-tracking")

print("Path to dataset files:", path)