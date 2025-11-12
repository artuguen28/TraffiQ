"""
Copyright (c) 2024 The D-FINE Authors. All Rights Reserved.
"""

import cv2
import numpy as np
import onnxruntime as ort
import torch
import torchvision.transforms as T
from PIL import Image, ImageDraw, ImageFont
from collections import Counter
import time


def resize_with_aspect_ratio(image, size, interpolation=Image.BILINEAR):
    """Resizes an image while maintaining aspect ratio and pads it."""
    original_width, original_height = image.size
    ratio = min(size / original_width, size / original_height)
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)
    image = image.resize((new_width, new_height), interpolation)

    new_image = Image.new("RGB", (size, size))
    new_image.paste(image, ((size - new_width) // 2, (size - new_height) // 2))
    return new_image, ratio, (size - new_width) // 2, (size - new_height) // 2



def draw(images, labels, boxes, scores, ratios, paddings, thrh=0.4, class_map=None):
    """Draw bounding boxes and return detected label counts."""
    result_images = []
    detected_counts = Counter()

    # Load font safely
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()

    for i, im in enumerate(images):
        draw = ImageDraw.Draw(im)
        scr = scores[i]
        mask = scr > thrh
        lab = labels[i][mask]
        box = boxes[i][mask]
        scr = scr[mask]

        ratio = ratios[i]
        pad_w, pad_h = paddings[i]

        for lbl, bb, sc in zip(lab, box, scr):
            lbl = int(lbl)
            detected_counts[lbl] += 1

            # Adjust bbox to original image size
            bb = [
                (bb[0] - pad_w) / ratio,
                (bb[1] - pad_h) / ratio,
                (bb[2] - pad_w) / ratio,
                (bb[3] - pad_h) / ratio,
            ]


            obj_cls = class_map[lbl] if class_map and lbl < len(class_map) else str(lbl)
            label_text = f"{obj_cls} {sc:.2f}"

            # Compute text size (compatible with Pillow 10+)
            if hasattr(draw, "textbbox"):  # Newer Pillow
                text_w, text_h = draw.textbbox((0, 0), label_text, font=font)[2:]
            else:  # Older Pillow
                text_w, text_h = draw.textsize(label_text, font=font)

            if obj_cls == 7:

                # Draw rectangle (thicker)
                draw.rectangle(bb, outline="red", width=4)

                # Draw text background
                text_bg = [bb[0], bb[1] - text_h - 4, bb[0] + text_w + 4, bb[1]]
                draw.rectangle(text_bg, fill="red")

                # Draw text
                draw.text((bb[0] + 2, bb[1] - text_h - 2), label_text, fill="white", font=font)

        result_images.append(im)

    return result_images, detected_counts


def process_image(sess, im_pil, class_map):
    resized_im_pil, ratio, pad_w, pad_h = resize_with_aspect_ratio(im_pil, 640)
    orig_size = torch.tensor([[resized_im_pil.size[1], resized_im_pil.size[0]]])
    transforms = T.Compose([T.ToTensor()])
    im_data = transforms(resized_im_pil).unsqueeze(0)

    output = sess.run(
        output_names=None,
        input_feed={"images": im_data.numpy(), "orig_target_sizes": orig_size.numpy()},
    )
    labels, boxes, scores = output

    result_images, detected_counts = draw([im_pil], labels, boxes, scores, [ratio], [(pad_w, pad_h)], class_map=class_map)
    result_images[0].save("onnx_result.jpg")

    print("\nDetected classes (image):")
    for lbl, count in detected_counts.items():
        name = class_map[lbl] if class_map and lbl < len(class_map) else str(lbl)
        print(f"  {name}: {count}")
    print("Saved as 'onnx_result.jpg'.")


def process_video(sess, video_path, class_map):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter("onnx_result.mp4", fourcc, fps, (orig_w, orig_h))

    total_counts = Counter()
    frame_count = 0
    start_time = time.time()

    print("Processing video frames...")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        resized_frame_pil, ratio, pad_w, pad_h = resize_with_aspect_ratio(frame_pil, 640)
        orig_size = torch.tensor([[resized_frame_pil.size[1], resized_frame_pil.size[0]]])
        transforms = T.Compose([T.ToTensor()])
        im_data = transforms(resized_frame_pil).unsqueeze(0)

        output = sess.run(
            output_names=None,
            input_feed={"images": im_data.numpy(), "orig_target_sizes": orig_size.numpy()},
        )
        labels, boxes, scores = output

        result_images, detected_counts = draw(
            [frame_pil], labels, boxes, scores, [ratio], [(pad_w, pad_h)], class_map=class_map
        )
        total_counts.update(detected_counts)

        frame = cv2.cvtColor(np.array(result_images[0]), cv2.COLOR_RGB2BGR)
        out.write(frame)
        frame_count += 1

        if frame_count % 10 == 0:
            elapsed = time.time() - start_time
            print(f"Processed {frame_count} frames ({frame_count / elapsed:.2f} FPS)...")

    cap.release()
    out.release()
    elapsed = time.time() - start_time
    print(f"\nVideo processing complete ({frame_count / elapsed:.2f} FPS). Saved as 'onnx_result.mp4'.")

    print("\nDetected classes (total):")
    for lbl, count in total_counts.items():
        name = class_map[lbl] if class_map and lbl < len(class_map) else str(lbl)
        print(f"  {name}: {count}")


def main(args):
    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    sess = ort.InferenceSession(args.onnx, providers=providers)
    print(f"Using device: {sess.get_providers()[0]}")

    # Load COCO or custom class map if needed
    class_map = [i for i in range(365)]  # Replace with your dataset's names

    input_path = args.input
    try:
        im_pil = Image.open(input_path).convert("RGB")
        process_image(sess, im_pil, class_map)
    except IOError:
        process_video(sess, input_path, class_map)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--onnx", type=str, required=True, help="Path to the ONNX model file.")
    parser.add_argument("--input", type=str, required=True, help="Path to the input image or video file.")
    args = parser.parse_args()
    main(args)
