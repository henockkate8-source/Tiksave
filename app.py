import os
import re
import tempfile

from flask import Flask, request, send_file, render_template_string, jsonify
import yt_dlp

app = Flask(__name__)

TIKTOK_RE = re.compile(r"^https?://([a-z0-9-]+\.)?tiktok\.com/", re.I)

PAGE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TikSave</title>
<style>
  :root { --bg:#0f1115; --card:#181b22; --txt:#f2f4f8; --mut:#9aa3b2; --acc:#25f4ee; --acc2:#fe2c55; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:system-ui,sans-serif; background:var(--bg); color:var(--txt);
         min-height:100vh; display:flex; align-items:center; justify-content:center; padding:16px; }
  main { width:100%; max-width:480px; background:var(--card); border-radius:16px; padding:24px; }
  h1 { margin:0 0 4px; font-size:1.6rem; }
  h1 span { color:var(--acc); }
  p.sub { margin:0 0 20px; color:var(--mut); font-size:.95rem; }
  input { width:100%; padding:14px; border-radius:10px; border:1px solid #2a2f3a;
          background:#0f1115; color:var(--txt); font-size:1rem; }
  button { width:100%; margin-top:12px; padding:14px; border:0; border-radius:10px; cursor:pointer;
           background:linear-gradient(90deg,var(--acc),var(--acc2)); color:#000; font-weight:700; font-size:1rem; }
  button:disabled { opacity:.6; cursor:wait; }
  #msg { margin-top:14px; min-height:1.2em; font-size:.9rem; color:var(--mut); }
  #msg.err { color:#ff6b81; }
  small { display:block; margin-top:18px; color:var(--mut); font-size:.75rem; line-height:1.4; }
</style>
</head>
<body>
<main>
  <h1>Tik<span>Save</span></h1>
  <p class="sub">Colle le lien d'une vidéo TikTok et télécharge-la sans logo.</p>
  <form id="f">
    <input id="url" type="url" placeholder="https://www.tiktok.com/@user/video/..." required>
    <button id="btn" type="submit">Télécharger</button>
  </form>
  <div id="msg"></div>
  <small>Utilise cet outil uniquement pour tes propres vidéos ou avec l'accord de leur auteur.
  Respecte les droits d'auteur et les conditions d'utilisation de TikTok.</small>
</main>
<script>
const f = document.getElementById('f'), btn = document.getElementById('btn'), msg = document.getElementById('msg');
f.addEventListener('submit', async (e) => {
  e.preventDefault();
  msg.className = ''; msg.textContent = 'Traitement en cours…'; btn.disabled = true;
  try {
    const r = await fetch('/download', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url: document.getElementById('url').value.trim()})
    });
    if (!r.ok) { const j = await r.json(); throw new Error(j.error || 'Erreur'); }
    const blob = await r.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'tiktok.mp4';
    document.body.appendChild(a); a.click(); a.remove();
    msg.textContent = 'Téléchargement lancé ✅';
  } catch (err) {
    msg.className = 'err'; msg.textContent = err.message;
  } finally { btn.disabled = false; }
});
</script>
</body>
</html>"""


@app.get("/")
def index():
    return render_template_string(PAGE)


@app.post("/download")
def download():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not TIKTOK_RE.match(url):
        return jsonify(error="Lien TikTok invalide."), 400

    tmp = tempfile.mkdtemp()
    opts = {
        "outtmpl": os.path.join(tmp, "%(id)s.%(ext)s"),
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "noplaylist": True,
        "max_filesize": 200 * 1024 * 1024,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
    except Exception:
        return jsonify(error="Impossible de récupérer cette vidéo (privée, supprimée ou lien incorrect)."), 422

    return send_file(path, as_attachment=True, download_name="tiktok.mp4", mimetype="video/mp4")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
