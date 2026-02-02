from pathlib import Path
import uuid
import uvicorn
import webbrowser
import threading

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from engine import run_calculation

# this just creates the path to uploads and outputs in the data folder
app_dir = Path(__file__).parent.resolve()
uploads= app_dir / "data" / "uploads"
outputs= app_dir / "data" / "outputs"

#for good order make sure that the file size isnt too big in this case i chose 10MB
maxUploadedBytes = 10 * 1024 * 1024  

#starts fast api
app = FastAPI()

#this is what creates the website with html and js.
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

  const res = await fetch("/run", { method: "POST", body: form });

  if (!res.ok) {
    // FastAPI returns JSON for HTTPException by default
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

# This is what runs when the user clicks the button "upload and download output.xlsx"
@app.post("/run")
async def run(file: UploadFile = File(...)):

    #if there is no file or it isnt of type .xlsx send error
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files allowed")

    #this is an asyncronous function so we have to wait the file to be read before anything else
    contents = await file.read()

    #just checks for the size of the file, we set max earlier to 10MB
    if len(contents) > maxUploadedBytes:
        raise HTTPException(status_code=413, detail=f"File too large (max {maxUploadedBytes} bytes)")

    #assign it a universally unique identifier
    job_id = str(uuid.uuid4())

    #adjusting the input and output path for the specific file
    input_path = uploads / f"{job_id}.xlsx"
    output_path = outputs / f"{job_id}_output.xlsx"

    #Writes the uploaded file bytes to disk
    input_path.write_bytes(contents)

    #now it runs the "calculations"/business logic which is defined in engine.py, and returns the relevant errors ocurred
    try:
        run_calculation(input_path, output_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) # the error explained xxx
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {type(e).__name__}: {e}") #returns a readable validation error

    #returns file to the client
    return FileResponse(
    path=output_path,
    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    filename="output.xlsx",
)

def open_browser():
    webbrowser.open("http://127.0.0.1:8000")


# This does such that when run it automatically opens in the browser
if __name__ == "__main__":
   threading.Timer(0.8, open_browser).start()
   uvicorn.run(app, host="0.0.0.0", port=8000)