import cv2
import os

def images_to_video(image_folder, output_path, fps=30):
    # Get all image files from the folder
    images = [img for img in os.listdir(image_folder)
              if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
    images.sort()  # Ensures frames are in the right order

    if not images:
        raise ValueError("No images found in the folder.")

    # Read the first image to get dimensions
    first_image_path = os.path.join(image_folder, images[0])
    frame = cv2.imread(first_image_path)
    height, width, _ = frame.shape

    # Define video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for MP4
    video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Write each image as a frame
    for img_name in images:
        img_path = os.path.join(image_folder, img_name)
        frame = cv2.imread(img_path)
        if frame is None:
            print(f"Warning: Could not read {img_path}. Skipping.")
            continue
        resized_frame = cv2.resize(frame, (width, height))
        video.write(resized_frame)

    video.release()
    print(f"Video saved to {output_path}")

# Example usage
if __name__ == "__main__":
    images_to_video(
        image_folder="/home/arthur/.cache/kagglehub/datasets/trainingdatapro/cars-video-object-tracking/versions/3/images",
        output_path="output_video.mp4",
        fps=30
    )
