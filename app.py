from pathlib import Path
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from engine import run_calculation


# -------------------------------------------------------------------
# Infrastructure / storage setup
# -------------------------------------------------------------------

# Cloud Run allows writing only to /tmp (ephemeral storage)
# This replaces your local ./data/uploads and ./data/outputs
uploads = Path("/tmp/uploads")
outputs = Path("/tmp/outputs")

# Make sure folders exist (important on Cloud Run)
uploads.mkdir(parents=True, exist_ok=True)
outputs.mkdir(parents=True, exist_ok=True)

# For good order make sure that the file size isnt too big
# in this case i chose 10MB
maxUploadedBytes = 10 * 1024 * 1024  


# -------------------------------------------------------------------
# Start FastAPI
# -------------------------------------------------------------------

app = FastAPI()


# -------------------------------------------------------------------
# Frontend (HTML + JS)
# -------------------------------------------------------------------

# This is what creates the website with html and js.
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Workflow MVP</title>
  <style>
    body { font-family: sans-serif; max-width: 720px; margin: 40px auto; }
    .card { padding: 16px; border: 1px solid #ddd; border-radius: 12px; }
    button { padding: 10px 14px; cursor: pointer; }
    input { margin: 10px 0; }
    #msg { margin-top: 12px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <h2>Double A1</h2>
  <p>Upload an <b>input.xlsx</b>. The server doubles the value in cell <b>A1</b> and returns <b>output.xlsx</b>.</p>

  <div class="card">
    <input id="file" type="file" accept=".xlsx" />
    <br/>
    <button onclick="upload()">Upload & Download output.xlsx</button>
    <div id="msg"></div>
  </div>

<script>
async function upload() {
  const fileInput = document.getElementById("file");
  const msg = document.getElementById("msg");
  msg.textContent = "";

  if (!fileInput.files.length) {
    msg.textContent = "Choose an .xlsx file first.";
    return;
  }

  const f = fileInput.files[0];
  if (!f.name.toLowerCase().endsWith(".xlsx")) {
    msg.textContent = "Only .xlsx files allowed.";
    return;
  }

  msg.textContent = "Uploading...";

  const form = new FormData();
  form.append("file", f);

  let res;
  try {
    res = await fetch("/run", { method: "POST", body: form });
  } catch (err) {
    msg.textContent = "Network error:\\n" + err;
    return;
  }

  if (!res.ok) {
    let text;
    try {
      const j = await res.json();
      text = j.detail ? String(j.detail) : JSON.stringify(j);
    } catch {
      text = await res.text();
    }
    msg.textContent = "Server error:\\n" + text;
    return;
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "output.xlsx";
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);

  msg.textContent = "Done. Download should have started.";
}
</script>
</body>
</html>
"""


# -------------------------------------------------------------------
# API endpoint (file upload + calculation)
# -------------------------------------------------------------------

# This is what runs when the user clicks the button
@app.post("/run")
async def run(file: UploadFile = File(...)):

    # If there is no file or it isnt of type .xlsx send error
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files allowed")

    # This is an asynchronous function so we have to wait
    # for the file to be read before anything else
    contents = await file.read()

    # Just checks for the size of the file
    if len(contents) > maxUploadedBytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {maxUploadedBytes} bytes)"
        )

    # Assign it a universally unique identifier
    job_id = str(uuid.uuid4())

    # Adjusting the input and output path for the specific file
    input_path = uploads / f"{job_id}.xlsx"
    output_path = outputs / f"{job_id}_output.xlsx"

    # Writes the uploaded file bytes to disk
    input_path.write_bytes(contents)

    # Run the "calculations"/business logic
    try:
        run_calculation(input_path, output_path)
    except ValueError as e:
        # Validation / user errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected server errors
        raise HTTPException(
            status_code=500,
            detail=f"Calculation failed: {type(e).__name__}: {e}"
        )

    # Return the output file to the client
    return FileResponse(
        path=output_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="output.xlsx",
    )
