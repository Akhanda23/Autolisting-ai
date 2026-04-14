from __future__ import annotations

import base64
import io
import random
from textwrap import dedent

from flask import Flask, jsonify, request
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

app = Flask(__name__)

INDEX_HTML = dedent(
    """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>AutoListing AI</title>
      <style>
        :root {
          --bg: #0b1220;
          --panel: #121b2d;
          --panel-2: #192338;
          --text: #eef4ff;
          --muted: #94a3b8;
          --accent: #1dd9a0;
          --border: rgba(255,255,255,0.08);
        }

        * { box-sizing: border-box; }

        body {
          margin: 0;
          font-family: Arial, Helvetica, sans-serif;
          background: radial-gradient(circle at top, #18263f 0%, #0b1220 45%, #080d16 100%);
          color: var(--text);
          min-height: 100vh;
        }

        .app {
          max-width: 1200px;
          margin: 0 auto;
          padding: 24px;
        }

        .topbar,
        .hero,
        .results {
          background: rgba(18, 27, 45, 0.95);
          border: 1px solid var(--border);
          border-radius: 18px;
          box-shadow: 0 18px 40px rgba(0,0,0,0.28);
        }

        .topbar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
          padding: 18px 22px;
          margin-bottom: 24px;
        }

        .brand {
          font-size: 1.2rem;
          font-weight: 800;
        }

        .brand span { color: var(--accent); }

        .pill {
          padding: 8px 14px;
          border-radius: 999px;
          background: rgba(29,217,160,0.1);
          color: var(--accent);
          border: 1px solid rgba(29,217,160,0.28);
          font-size: 0.8rem;
          font-weight: 700;
        }

        .hero {
          padding: 42px 24px;
          text-align: center;
          margin-bottom: 24px;
        }

        .hero h1 {
          margin: 0 0 14px;
          font-size: clamp(2rem, 5vw, 4rem);
          line-height: 1;
        }

        .hero h1 span { color: var(--accent); }

        .hero p {
          max-width: 740px;
          margin: 0 auto 24px;
          color: var(--muted);
          line-height: 1.7;
        }

        .controls {
          display: flex;
          gap: 12px;
          justify-content: center;
          flex-wrap: wrap;
          margin-bottom: 16px;
        }

        .dropzone {
          max-width: 760px;
          margin: 0 auto;
          padding: 28px 18px;
          border: 2px dashed rgba(29,217,160,0.34);
          border-radius: 18px;
          background: rgba(29,217,160,0.04);
          cursor: pointer;
        }

        .dropzone.dragover {
          border-color: var(--accent);
          background: rgba(29,217,160,0.08);
        }

        select,
        button,
        input[type="file"] {
          border-radius: 10px;
          border: 1px solid var(--border);
          padding: 11px 14px;
          background: var(--panel-2);
          color: var(--text);
          font-size: 0.95rem;
        }

        button {
          cursor: pointer;
          font-weight: 700;
        }

        .primary {
          background: var(--accent);
          color: #08120e;
          border-color: transparent;
        }

        .results {
          padding: 20px;
          display: none;
        }

        .progress-wrap {
          margin-bottom: 18px;
        }

        .progress-bar {
          width: 100%;
          height: 8px;
          background: #0c1423;
          border-radius: 999px;
          overflow: hidden;
          border: 1px solid var(--border);
        }

        .progress-fill {
          width: 0%;
          height: 100%;
          background: linear-gradient(90deg, #1dd9a0, #80ffe0);
          transition: width 0.3s ease;
        }

        .status {
          margin-top: 8px;
          color: var(--muted);
          font-size: 0.92rem;
        }

        .grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 18px;
        }

        .card {
          background: var(--panel-2);
          border: 1px solid var(--border);
          border-radius: 16px;
          overflow: hidden;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
          padding: 14px 16px;
          border-bottom: 1px solid var(--border);
        }

        .card-title {
          font-weight: 800;
        }

        .card-body {
          padding: 16px;
        }

        img.output {
          width: 100%;
          border-radius: 12px;
          display: block;
          background: #0b1220;
          border: 1px solid var(--border);
        }

        .viewer-stage {
          position: relative;
          width: 100%;
          aspect-ratio: 16 / 9;
          overflow: hidden;
          border-radius: 12px;
          border: 1px solid var(--border);
          background: #0b1220;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .viewer-stage img {
          max-width: 90%;
          max-height: 90%;
          transition: transform 0.12s linear;
          transform-style: preserve-3d;
          filter: drop-shadow(0 16px 26px rgba(0,0,0,0.32));
          user-select: none;
          pointer-events: none;
        }

        .viewer-hint {
          font-size: 0.86rem;
          color: var(--muted);
          margin-top: 10px;
        }

        .tags {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          margin-bottom: 14px;
        }

        .tags span {
          font-size: 0.8rem;
          padding: 6px 10px;
          border-radius: 999px;
          color: var(--muted);
          background: rgba(255,255,255,0.05);
          border: 1px solid var(--border);
        }

        .price {
          font-size: 1.8rem;
          font-weight: 800;
          color: var(--accent);
          margin-bottom: 12px;
        }

        .description {
          white-space: pre-wrap;
          line-height: 1.75;
          color: var(--text);
          background: #0d1423;
          border: 1px solid var(--border);
          border-radius: 12px;
          padding: 14px;
        }

        .hidden {
          display: none !important;
        }

        @media (max-width: 900px) {
          .grid {
            grid-template-columns: 1fr;
          }
        }
      </style>
    </head>
    <body>
      <div class="app">
        <div class="topbar">
          <div class="brand">Auto<span>Listing</span> AI</div>
          <div class="pill">Single File Demo</div>
        </div>

        <section class="hero">
          <h1>Car only. <span>Studio look.</span></h1>
          <p>
            Upload one car image to generate a cleaner studio-style background, privacy-safe number plate output,
            a simulated 360-style rotatable viewer, and a marketplace-ready description.
          </p>

          <div class="controls">
            <select id="bgTheme">
              <option value="studio">Studio Neon</option>
              <option value="sunset">Sunset Glow</option>
              <option value="night">Midnight Luxe</option>
            </select>

            <select id="plateMode">
              <option value="censor">Censor Plate</option>
              <option value="remove">Remove Plate</option>
            </select>

            <button id="chooseBtn">Choose Image</button>
            <button id="runBtn" class="primary">Process Image</button>
          </div>

          <div id="dropzone" class="dropzone">
            Drag and drop your car image here, or click Choose Image.
            <input id="fileInput" type="file" accept="image/*" class="hidden" />
          </div>
        </section>

        <section id="results" class="results">
          <div class="progress-wrap">
            <div class="progress-bar"><div id="progressFill" class="progress-fill"></div></div>
            <div id="statusText" class="status">Waiting for image...</div>
          </div>

          <div class="grid">
            <div class="card">
              <div class="card-header"><div class="card-title">Studio Output</div></div>
              <div class="card-body">
                <img id="studioImg" class="output" alt="Studio output" />
              </div>
            </div>

            <div class="card">
              <div class="card-header"><div class="card-title">Protected Output</div></div>
              <div class="card-body">
                <img id="protectedImg" class="output" alt="Protected output" />
              </div>
            </div>

            <div class="card">
              <div class="card-header"><div class="card-title">360-Style Viewer</div></div>
              <div class="card-body">
                <div id="viewerStage" class="viewer-stage">
                  <img id="viewerImg" alt="Rotatable car" />
                </div>
                <div class="viewer-hint">Drag left and right to simulate a 360-style turntable effect.</div>
              </div>
            </div>

            <div class="card">
              <div class="card-header"><div class="card-title">Listing Description</div></div>
              <div class="card-body">
                <div id="price" class="price">$0</div>
                <div id="tags" class="tags"></div>
                <div id="description" class="description"></div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <script>
        const fileInput = document.getElementById('fileInput');
        const chooseBtn = document.getElementById('chooseBtn');
        const runBtn = document.getElementById('runBtn');
        const dropzone = document.getElementById('dropzone');
        const results = document.getElementById('results');
        const progressFill = document.getElementById('progressFill');
        const statusText = document.getElementById('statusText');
        const studioImg = document.getElementById('studioImg');
        const protectedImg = document.getElementById('protectedImg');
        const viewerImg = document.getElementById('viewerImg');
        const viewerStage = document.getElementById('viewerStage');
        const description = document.getElementById('description');
        const tags = document.getElementById('tags');
        const price = document.getElementById('price');
        const bgTheme = document.getElementById('bgTheme');
        const plateMode = document.getElementById('plateMode');

        let selectedFile = null;
        let dragActive = false;
        let draggingViewer = false;
        let lastX = 0;
        let rot = 0;

        function setProgress(value, text) {
          progressFill.style.width = value + '%';
          statusText.textContent = text;
        }

        chooseBtn.addEventListener('click', () => fileInput.click());
        dropzone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => {
          selectedFile = e.target.files[0] || null;
          if (selectedFile) {
            statusText.textContent = 'Selected: ' + selectedFile.name;
          }
        });

        dropzone.addEventListener('dragover', (e) => {
          e.preventDefault();
          if (!dragActive) {
            dragActive = true;
            dropzone.classList.add('dragover');
          }
        });

        dropzone.addEventListener('dragleave', () => {
          dragActive = false;
          dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', (e) => {
          e.preventDefault();
          dragActive = false;
          dropzone.classList.remove('dragover');
          selectedFile = e.dataTransfer.files[0] || null;
          if (selectedFile) {
            statusText.textContent = 'Selected: ' + selectedFile.name;
          }
        });

        runBtn.addEventListener('click', async () => {
          if (!selectedFile) {
            alert('Please choose an image first.');
            return;
          }

          results.style.display = 'block';
          setProgress(10, 'Uploading image...');

          const form = new FormData();
          form.append('file', selectedFile);
          form.append('bg_theme', bgTheme.value);
          form.append('plate_mode', plateMode.value);

          try {
            setProgress(30, 'Processing image...');
            const response = await fetch('/process', {
              method: 'POST',
              body: form,
            });

            setProgress(80, 'Preparing results...');
            const data = await response.json();

            studioImg.src = data.studio_image;
            protectedImg.src = data.protected_image;
            viewerImg.src = data.viewer_image;
            description.textContent = data.description;
            price.textContent = '$' + data.price.toLocaleString();
            tags.innerHTML = data.tags.map(tag => `<span>${tag}</span>`).join('');

            rot = 0;
            viewerImg.style.transform = 'rotateY(0deg)';
            setProgress(100, 'Done.');
          } catch (error) {
            setProgress(0, 'Something went wrong while processing the image.');
            console.error(error);
          }
        });

        viewerStage.addEventListener('mousedown', (e) => {
          draggingViewer = true;
          lastX = e.clientX;
        });

        window.addEventListener('mousemove', (e) => {
          if (!draggingViewer) return;
          const dx = e.clientX - lastX;
          lastX = e.clientX;
          rot += dx * 0.8;
          viewerImg.style.transform = `perspective(900px) rotateY(${rot}deg) scale(1.02)`;
        });

        window.addEventListener('mouseup', () => {
          draggingViewer = false;
        });
      </script>
    </body>
    </html>
    """
)


def image_to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill, outline=None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def create_studio_background(width: int, height: int, theme: str) -> Image.Image:
    bg = Image.new("RGBA", (width, height), (10, 14, 22, 255))
    draw = ImageDraw.Draw(bg)

    if theme == "sunset":
        top = (88, 42, 102)
        mid = (255, 128, 82)
        bottom = (26, 24, 42)
    elif theme == "night":
        top = (8, 18, 34)
        mid = (16, 40, 70)
        bottom = (5, 8, 14)
    else:
        top = (14, 26, 48)
        mid = (30, 56, 96)
        bottom = (8, 12, 18)

    for y in range(height):
        t = y / max(1, height - 1)
        if t < 0.5:
            local = t / 0.5
            color = tuple(int(top[i] + (mid[i] - top[i]) * local) for i in range(3))
        else:
            local = (t - 0.5) / 0.5
            color = tuple(int(mid[i] + (bottom[i] - mid[i]) * local) for i in range(3))
        draw.line((0, y, width, y), fill=color + (255,))

    floor = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    floor_draw = ImageDraw.Draw(floor)
    floor_draw.ellipse(
        (int(width * 0.14), int(height * 0.66), int(width * 0.86), int(height * 0.96)),
        fill=(255, 255, 255, 24),
    )
    floor = floor.filter(ImageFilter.GaussianBlur(32))
    bg.alpha_composite(floor)

    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    if theme == "sunset":
        glow_color = (255, 196, 110, 72)
    elif theme == "night":
        glow_color = (90, 255, 210, 60)
    else:
        glow_color = (86, 194, 255, 66)

    glow_draw.ellipse(
        (int(width * 0.22), int(height * 0.10), int(width * 0.78), int(height * 0.74)),
        fill=glow_color,
    )
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    bg.alpha_composite(glow)

    return bg


def approximate_car_only(image: Image.Image) -> Image.Image:
    """
    Demo-only approximation.
    Keeps a central band as the "car" and softens the rest through transparency,
    so the output behaves like a rough cutout without requiring a segmentation model.
    """
    image = image.convert("RGBA")
    width, height = image.size

    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)

    left = int(width * 0.08)
    top = int(height * 0.18)
    right = int(width * 0.92)
    bottom = int(height * 0.84)

    draw.rounded_rectangle((left, top, right, bottom), radius=int(min(width, height) * 0.05), fill=255)

    mask = mask.filter(ImageFilter.GaussianBlur(radius=max(8, int(min(width, height) * 0.03))))

    result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    result.alpha_composite(image)
    result.putalpha(mask)
    return result


def enhance_car(car_only: Image.Image) -> Image.Image:
    rgb = car_only.convert("RGBA")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.15)
    rgb = ImageEnhance.Color(rgb).enhance(1.08)
    rgb = ImageEnhance.Sharpness(rgb).enhance(1.2)
    return rgb


def build_studio_scene(car_only: Image.Image, theme: str) -> Image.Image:
    car_only = enhance_car(car_only)
    car_width, car_height = car_only.size

    canvas_width = max(1280, car_width + 280)
    canvas_height = int(canvas_width * 0.64)

    background = create_studio_background(canvas_width, canvas_height, theme)

    scale = min((canvas_width * 0.74) / car_width, (canvas_height * 0.58) / car_height)
    resized_car = car_only.resize((int(car_width * scale), int(car_height * scale)), Image.LANCZOS)

    x = (canvas_width - resized_car.width) // 2
    y = int(canvas_height * 0.18)

    shadow = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse(
        (x + 90, y + resized_car.height - 8, x + resized_car.width - 90, y + resized_car.height + 42),
        fill=(0, 0, 0, 90),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    background.alpha_composite(shadow)

    rim = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
    rim_draw = ImageDraw.Draw(rim)
    rim_draw.ellipse(
        (x - 40, y - 24, x + resized_car.width + 40, y + resized_car.height + 24),
        fill=(120, 255, 220, 36),
    )
    rim = rim.filter(ImageFilter.GaussianBlur(32))
    background.alpha_composite(rim)

    background.alpha_composite(resized_car, (x, y))
    return background


def protect_number_plate(image: Image.Image, plate_mode: str) -> Image.Image:
    output = image.copy().convert("RGBA")
    draw = ImageDraw.Draw(output)
    width, height = output.size

    x1 = int(width * 0.43)
    y1 = int(height * 0.61)
    x2 = int(width * 0.57)
    y2 = int(height * 0.67)

    if plate_mode == "remove":
        rounded_rect(
            draw,
            (x1, y1, x2, y2),
            radius=10,
            fill=(82, 84, 88, 235),
            outline=(140, 140, 145, 110),
            width=2,
        )
        rounded_rect(
            draw,
            (x1 + 14, y1 + 8, x2 - 14, y1 + 18),
            radius=5,
            fill=(140, 140, 145, 60),
        )
    else:
        rounded_rect(
            draw,
            (x1, y1, x2, y2),
            radius=10,
            fill=(14, 18, 22, 240),
            outline=(29, 217, 160, 120),
            width=2,
        )
        text = "PLATE HIDDEN"
        font_y = (y1 + y2) // 2 - 6
        draw.text((x1 + 18, font_y), text, fill=(29, 217, 160, 255))

    return output


def generate_description() -> tuple[str, int, list[str]]:
    makes = ["Toyota", "Honda", "Mazda", "Ford", "BMW", "Hyundai", "Nissan"]
    models = ["Camry", "Civic", "CX-5", "Ranger", "320i", "Tucson", "X-Trail"]
    colours = ["Pearl White", "Jet Black", "Graphite Grey", "Deep Blue", "Metallic Red"]
    bodies = ["Sedan", "SUV", "Hatchback", "Ute"]
    engines = ["2.0L petrol engine", "2.5L petrol engine", "hybrid powertrain", "2.2L turbo diesel"]
    drives = ["FWD", "RWD", "AWD"]
    transmissions = ["automatic", "manual", "CVT automatic"]

    year = random.choice([2019, 2020, 2021, 2022, 2023, 2024])
    make = random.choice(makes)
    model = random.choice(models)
    colour = random.choice(colours)
    body = random.choice(bodies)
    engine = random.choice(engines)
    drive = random.choice(drives)
    transmission = random.choice(transmissions)
    kms = random.randint(18, 95) * 1000
    seats = random.choice([4, 5, 7])
    price = random.randint(18, 58) * 1000

    tags = [
        str(year),
        make,
        model,
        colour,
        body,
        engine,
        transmission,
        drive,
        f"{kms:,} km",
        f"{seats} seats",
    ]

    description = (
        f"{year} {make} {model} presented in {colour.lower()} with a clean, sharp appearance and strong visual presence.\n\n"
        f"This {body.lower()} is matched with a {engine} and {transmission}, making it a well-rounded option for buyers who want a vehicle that looks great in person and even better in a marketplace listing.\n\n"
        f"Highlights include:\n"
        f"- Approximately {kms:,} km travelled\n"
        f"- {drive} drivetrain\n"
        f"- {seats} seat configuration\n"
        f"- Studio-style prepared images\n"
        f"- Number plate fully protected for privacy\n\n"
        f"The vehicle has been prepared to stand out visually with a cleaner studio presentation, helping attract stronger buyer attention online. Serious enquiries welcome."
    )

    return description, price, tags


@app.get("/")
def index():
    return INDEX_HTML


@app.post("/process")
def process():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["file"]
    bg_theme = request.form.get("bg_theme", "studio")
    plate_mode = request.form.get("plate_mode", "censor")

    try:
        image = Image.open(file.stream).convert("RGBA")
    except Exception:
        return jsonify({"error": "Invalid image file."}), 400

    car_only = approximate_car_only(image)
    studio = build_studio_scene(car_only, bg_theme)
    protected = protect_number_plate(studio, plate_mode)
    viewer_image = studio.copy()

    description, price, tags = generate_description()

    return jsonify(
        {
            "studio_image": image_to_data_url(studio),
            "protected_image": image_to_data_url(protected),
            "viewer_image": image_to_data_url(viewer_image),
            "description": description,
            "price": price,
            "tags": tags,
        }
    )


if __name__ == "__main__":
    print("AutoListing AI running at http://127.0.0.1:5000")
    app.run(debug=True)
