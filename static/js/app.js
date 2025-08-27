// Simple canvas preview script
const nameInput = document.getElementById("name");
const fatherInput = document.getElementById("father");
const dobInput = document.getElementById("dob");
const villageInput = document.getElementById("village");
const districtInput = document.getElementById("district");
const notesInput = document.getElementById("notes");
const photoInput = document.getElementById("photo");
const previewBtn = document.getElementById("previewBtn");

const frontCanvas = document.getElementById("frontCanvas");
const backCanvas = document.getElementById("backCanvas");
const fctx = frontCanvas.getContext("2d");
const bctx = backCanvas.getContext("2d");

function drawFront(img) {
  // clear
  fctx.clearRect(0,0,frontCanvas.width, frontCanvas.height);
  // background
  fctx.fillStyle = "#ffffff";
  fctx.fillRect(0,0,frontCanvas.width, frontCanvas.height);
  // header
  fctx.fillStyle = "#0c7a3c";
  fctx.fillRect(0,0,frontCanvas.width,90);
  fctx.fillStyle = "#fff";
  fctx.font = "28px sans-serif";
  fctx.fillText("Kisan Identity Card", 20, 45);

  // name & details left
  fctx.fillStyle = "#000";
  fctx.font = "20px sans-serif";
  fctx.fillText("Name:", 20, 120);
  fctx.font = "26px sans-serif";
  fctx.fillText(nameInput.value || "-", 20, 150);

  fctx.font = "18px sans-serif";
  fctx.fillText("Father / Husband:", 20, 190);
  fctx.font = "20px sans-serif";
  fctx.fillText(fatherInput.value || "-", 20, 220);

  fctx.font = "18px sans-serif";
  fctx.fillText("DOB:", 20, 260);
  fctx.font = "20px sans-serif";
  fctx.fillText(dobInput.value || "-", 20, 290);

  fctx.fillText("Village:", 20, 340);
  fctx.font = "20px sans-serif";
  fctx.fillText(villageInput.value || "-", 20, 370);

  fctx.font = "18px sans-serif";
  fctx.fillText("District:", 20, 410);
  fctx.font = "20px sans-serif";
  fctx.fillText(districtInput.value || "-", 20, 440);

  // photo box right
  const pw = 200;
  const ph = 240;
  const px = frontCanvas.width - pw - 20;
  const py = 110;
  fctx.strokeStyle = "#000";
  fctx.strokeRect(px, py, pw, ph);
  if (img) {
    // fit image into box
    const scale = Math.min(pw / img.width, ph / img.height);
    const iw = img.width * scale;
    const ih = img.height * scale;
    fctx.drawImage(img, px + (pw-iw)/2, py + (ph-ih)/2, iw, ih);
  }
  // footer
  fctx.fillStyle = "#666";
  fctx.font = "16px sans-serif";
  fctx.fillText("Issue Date: " + (document.getElementById("issue_date").value || new Date().toISOString().slice(0,10)), 20, frontCanvas.height - 30);
}

function drawBack() {
  bctx.clearRect(0,0,backCanvas.width, backCanvas.height);
  bctx.fillStyle = "#f5f5f5";
  bctx.fillRect(0,0,backCanvas.width, backCanvas.height);
  bctx.fillStyle = "#0c7a3c";
  bctx.fillRect(0,0,backCanvas.width,90);
  bctx.fillStyle = "#fff";
  bctx.font = "24px sans-serif";
  bctx.fillText("Kisan Identity Card - Details", 20, 45);

  bctx.fillStyle = "#000";
  bctx.font = "18px sans-serif";
  bctx.fillText("Notes:", 20, 120);
  bctx.font = "16px sans-serif";

  // wrap notes
  const txt = notesInput.value || "No additional notes.";
  const words = txt.split(" ");
  let line = "";
  let y = 150;
  for (let i=0;i<words.length;i++){
    const test = line + words[i] + " ";
    const metrics = bctx.measureText(test);
    if (metrics.width > backCanvas.width - 60) {
      bctx.fillText(line, 20, y);
      line = words[i] + " ";
      y += 24;
    } else {
      line = test;
    }
  }
  if (line) bctx.fillText(line, 20, y);

  // placeholder QR box
  const qx = backCanvas.width - 220;
  const qy = backCanvas.height - 220;
  bctx.strokeStyle = "#000";
  bctx.strokeRect(qx, qy, 200, 200);
  bctx.font = "18px sans-serif";
  bctx.fillText("QR CODE", qx+50, qy+110);
}

let previewImage = null;

photoInput.addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) {
    previewImage = null;
    drawFront(null);
    return;
  }
  const reader = new FileReader();
  reader.onload = function(evt){
    const img = new Image();
    img.onload = function(){
      previewImage = img;
      drawFront(previewImage);
    };
    img.src = evt.target.result;
  };
  reader.readAsDataURL(file);
});

function renderPreview(){
  drawFront(previewImage);
  drawBack();
}

previewBtn.addEventListener("click", (e)=> {
  renderPreview();
});

// auto-render once page loads
window.addEventListener("load", ()=> {
  renderPreview();
});
