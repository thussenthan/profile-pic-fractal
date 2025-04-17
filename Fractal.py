import time
from PIL import Image, ImageDraw
import numpy as np
import math

def create_l_system(iters, axiom, rules):
    start_string = axiom
    for _ in range(iters):
        end_string = "".join(rules.get(ch, ch) for ch in start_string)
        start_string = end_string
    return start_string

def calc_length_height(instructions, angle, correction_angle):
    current_angle = correction_angle
    x_offset = 0
    y_offset = 0
    min_x = 0
    min_y = 0
    max_x = 0
    max_y = 0
    for inst in instructions:
        if inst == "F":
            x_offset += math.cos(math.radians(current_angle))
            y_offset += math.sin(math.radians(current_angle))
        elif inst == "B":
            x_offset -= math.cos(math.radians(current_angle))
            y_offset -= math.sin(math.radians(current_angle))
        elif inst == "+":
            current_angle -= angle
        elif inst == "-":
            current_angle += angle
        min_x = min(min_x, x_offset)
        min_y = min(min_y, y_offset)
        max_x = max(max_x, x_offset)
        max_y = max(max_y, y_offset)
    
    width = max_x - min_x
    height = max_y - min_y
    return width, height, -min_x, -min_y

def draw_l_system_on_overlay(draw, instructions, base_angle, step, start_pos, correction_angle):
    x, y = start_pos
    angle = correction_angle
    for cmd in instructions:
        if cmd == "F":
            new_x = x + step * math.cos(math.radians(angle))
            new_y = y + step * math.sin(math.radians(angle))
            draw.line([(x, y), (new_x, new_y)], fill=(255,0,0,255), width=2)
            x, y = new_x, new_y
        elif cmd == "B":
            new_x = x - step * math.cos(math.radians(angle))
            new_y = y - step * math.sin(math.radians(angle))
            draw.line([(x, y), (new_x, new_y)], fill=(255,0,0,255), width=2)
            x, y = new_x, new_y
        elif cmd == "+":
            angle -= base_angle
        elif cmd == "-":
            angle += base_angle
        # ignore other symbols

def distort_image_with_fractal(image, overlay, amplitude):
    # Convert images to numpy arrays.
    img_arr = np.array(image)
    overlay_arr = np.array(overlay)
    # Use the red channel of the fractal overlay as our indicator.
    red = overlay_arr[:, :, 0].astype(np.float32) / 255.0
    # Compute displacements (both x and y in this example).
    dx = (red - 0.5) * amplitude
    dy = (red - 0.5) * amplitude
    
    height, width = red.shape
    grid_x, grid_y = np.meshgrid(np.arange(width), np.arange(height))
    # Map to new coordinates using nearest neighbor.
    new_x = np.clip(np.round(grid_x + dx), 0, width - 1).astype(np.int32)
    new_y = np.clip(np.round(grid_y + dy), 0, height - 1).astype(np.int32)
    
    distorted = img_arr[new_y, new_x]
    return Image.fromarray(distorted)

def main():
    input_image_path = "your_image.jpg"  # Replace with the path to your image
    current_time = time.strftime("%Y%m%d_%H%M%S")
    output_image_path = f"output_{current_time}.png"

    try:
        image = Image.open(input_image_path).convert("RGBA")
    except Exception as e:
        print("Error loading image:", e)
        return

    # -- L-system parameters --
    axiom = "FX+FX+FX"
    rules = {"X": "X+YF+", "Y": "-FX-Y"}
    iterations = 15
    base_angle = 90
    correction_angle = 45 * iterations

    # Generate the instruction string and calculate bounds.
    instructions = create_l_system(iterations, axiom, rules)
    fractal_width, fractal_height, offset_x, offset_y = calc_length_height(instructions, base_angle, correction_angle)

    # -- Determine drawing scale --
    margin = 35  # margin around the fractal
    img_width, img_height = image.size
    scale_x = (img_width - 2 * margin) / fractal_width if fractal_width else 1
    scale_y = (img_height - 2 * margin) / fractal_height if fractal_height else 1
    step = min(scale_x, scale_y)

    # Define offset points for the fractal
    center_1 = (560, 600)

    # ---- ONE FRACTAL PASS ----
    overlay1 = Image.new("RGBA", image.size, (0,0,0,0))
    draw_overlay1 = ImageDraw.Draw(overlay1)
    draw_l_system_on_overlay(draw_overlay1, instructions, base_angle, step, center_1, correction_angle)

    # Distort the image with the single fractal overlay
    amplitude = 100  # adjust distortion strength as desired
    final_distorted_1 = distort_image_with_fractal(image, overlay1, amplitude)

    final_distorted_1.save(output_image_path)
    print(f"Fractal distorted image saved as {output_image_path}")

if __name__ == "__main__":
    main()
