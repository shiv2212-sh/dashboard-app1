# import threading, socket, sqlite3, json, io, csv, datetime, os, tempfile
# from flask import Flask, jsonify, render_template, send_file, request
# from waitress import serve
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors
# import os
# from waitress import serve
# import psutil



# DB_FILE = r"C:\Users\shivs\PyCharmMiscProject\client-dashboard-app\python\server_data.db"
# TEMPLATE_DIR = os.path.join(os.path.dirname(DB_FILE), "templates")

# TCP_HOST = "0.0.0.0"
# TCP_PORT = 9002

# app = Flask(__name__, template_folder=TEMPLATE_DIR)
# shutdown_flag = threading.Event()

# # ---------------- DATABASE ----------------
# def init_db():
#     os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()

#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS clients (
#         client_uuid TEXT PRIMARY KEY,
#         mac_address TEXT,
#         hostname TEXT,
#         last_seen TEXT,
#         client_ip TEXT,
#         hardware_info TEXT,
#         installed_apps TEXT
#     )""")

#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS app_history (
#         client_uuid TEXT,
#         app_name TEXT,
#         version TEXT,
#         status TEXT,
#         time TEXT
#     )""")

#     con.commit()
#     con.close()


# def upsert_client(data, ip):
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()

#     cur.execute("""
#     INSERT INTO clients VALUES (?, ?, ?, ?, ?, ?, ?)
#     ON CONFLICT(client_uuid) DO UPDATE SET
#         mac_address=excluded.mac_address,
#         hostname=excluded.hostname,
#         last_seen=excluded.last_seen,
#         client_ip=excluded.client_ip,
#         hardware_info=excluded.hardware_info,
#         installed_apps=excluded.installed_apps
#     """, (data["uuid"], data["mac"], data["hostname"],
#           data["timestamp"], ip, data["hardware"], data["apps"]))

#     for line in data["apps"].splitlines():
#         if "|" in line:
#             name, version, install_date, _ = line.split("|", 3)
#             time_val = install_date if install_date != "-" else data["timestamp"]
#             cur.execute("INSERT INTO app_history VALUES (?,?,?,?,?)",
#                         (data["uuid"], name, version, "Installed", time_val))

#     con.commit()
#     con.close()


# # ---------------- TCP SERVER ----------------
# def recv_line(sock):
#     data = b""
#     while not data.endswith(b"\n"):
#         p = sock.recv(1)
#         if not p: return None
#         data += p
#     return data.decode().strip()


# def recv_exact(sock, n):
#     data = b""
#     while len(data) < n:
#         p = sock.recv(n - len(data))
#         if not p: return None
#         data += p
#     return data


# def recv_text(sock):
#     l = recv_line(sock)
#     if not l: return None
#     payload = recv_exact(sock, int(l))
#     return payload.decode() if payload else None


# def parse_text_data(text):
#     lines = text.splitlines()
#     data = {"hardware": "", "apps": ""}
#     mode = None
#     for line in lines:
#         if line.startswith("CLIENT_UUID:"): data["uuid"] = line.split(":",1)[1].strip()
#         elif line.startswith("MAC_ADDRESS:"): data["mac"] = line.split(":",1)[1].strip()
#         elif line.startswith("HOSTNAME:"): data["hostname"] = line.split(":",1)[1].strip()
#         elif line.startswith("TIMESTAMP:"): data["timestamp"] = line.split(":",1)[1].strip()
#         elif line.startswith("=== HARDWARE"): mode="hw"
#         elif line.startswith("=== APPLICATIONS"): mode="apps"
#         elif mode=="hw": data["hardware"] += line + "\n"
#         elif mode=="apps": data["apps"] += line + "\n"
#     return data


# def handle_client(sock, addr):
#     ip,_ = addr
#     cmd = recv_line(sock)
#     if cmd != "get apps":
#         sock.close()
#         return
#     text = recv_text(sock)
#     data = parse_text_data(text)
#     if "uuid" in data:
#         upsert_client(data, ip)
#     sock.sendall(b"OK\n")
#     sock.close()


# def tcp_server():
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     s.bind((TCP_HOST, TCP_PORT))
#     s.listen(5)
#     print(f"[+] TCP listening {TCP_HOST}:{TCP_PORT}")
#     while not shutdown_flag.is_set():
#         try:
#             s.settimeout(1)
#             c,addr = s.accept()
#             threading.Thread(target=handle_client, args=(c,addr), daemon=True).start()
#         except socket.timeout:
#             continue
#     s.close()


# # ---------------- HELPERS ----------------
# def safe_json(v):
#     try:
#         return json.loads(v)
#     except:
#         return v.splitlines()


# def status_from_last_seen(ts):
#     try:
#         t = datetime.datetime.strptime(ts,"%Y-%m-%d %H:%M:%S")
#         return "Online" if (datetime.datetime.now()-t).seconds<=60 else "Offline"
#     except:
#         return "Offline"


# # ---------------- FLASK ROUTES ----------------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")


# @app.route("/api/clients")
# def api_clients():
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients")
#     rows = cur.fetchall()
#     con.close()

#     return jsonify([{
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "last_seen":r[3],
#         "ip":r[4],
#         "status":status_from_last_seen(r[3])
#     } for r in rows])


# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=?", (uuid,))
#     r = cur.fetchone()
#     con.close()

#     return jsonify({
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "last_seen":r[3],
#         "ip":r[4],
#         "hardware":safe_json(r[5]),
#         "apps":safe_json(r[6])
#     })


# @app.route("/export/pdf/<uuid>")
# def export_pdf(uuid):
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=?", (uuid,))
#     r = cur.fetchone()
#     con.close()

#     if not r:
#         return "Client not found", 404

#     fd, path = tempfile.mkstemp(suffix=".pdf")
#     os.close(fd)

#     doc = SimpleDocTemplate(path, pagesize=A4)
#     styles = getSampleStyleSheet()
#     elements = []

#     elements.append(Paragraph("Client Report", styles["Title"]))
#     elements.append(Spacer(1, 12))

#     info = [["Field","Value"],
#             ["UUID",r[0]],["MAC",r[1]],["Hostname",r[2]],
#             ["Last Seen",r[3]],["IP",r[4]]]

#     t1 = Table(info, colWidths=[120,350])
#     t1.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),
#                             ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
#     elements.append(t1); elements.append(Spacer(1,20))

#     elements.append(Paragraph("Hardware", styles["Heading2"]))
#     hw = [["Component"]] + [[l] for l in safe_json(r[5])]
#     t2 = Table(hw, colWidths=[470])
#     t2.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black)]))
#     elements.append(t2); elements.append(Spacer(1,20))

#     elements.append(Paragraph("Applications", styles["Heading2"]))
#     apps = [["Name","Version","Date","Size"]]
#     for l in safe_json(r[6]):
#         if "|" in l: apps.append(l.split("|",3))
#     t3 = Table(apps, colWidths=[180,90,100,100])
#     t3.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),
#                             ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
#     elements.append(t3)

#     doc.build(elements)

#     return send_file(path, as_attachment=True,
#                      mimetype="application/pdf",
#                      download_name=f"{uuid}.pdf")


# @app.route("/shutdown", methods=["POST"])
# def shutdown():
#     shutdown_flag.set()
#     os._exit(0)


# # ---------------- RUN ----------------

# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 9001))
#     serve(app, host="0.0.0.0", port=port)







# from flask import Flask, jsonify, render_template, request, send_file, Response
# import os, json, datetime, psycopg2, tempfile, csv
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.pagesizes import A4
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors

# DATABASE_URL = os.environ.get("DATABASE_URL")

# app = Flask(__name__, template_folder="templates")

# # ---------------- DATABASE ----------------
# def get_db():
#     return psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=5)

# def init_db():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS clients (
#         client_uuid TEXT PRIMARY KEY,
#         mac_address TEXT,
#         hostname TEXT,
#         last_seen TEXT,
#         client_ip TEXT,
#         hardware_info TEXT,
#         installed_apps TEXT
#     )
#     """)
#     con.commit()
#     con.close()

# # ---------------- HELPERS ----------------
# def safe_json(v):
#     try:
#         return json.loads(v)
#     except:
#         return v

# def status_from_last_seen(ts):
#     try:
#         t = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
#         return "Online" if (datetime.datetime.now() - t).seconds <= 60 else "Offline"
#     except:
#         return "Offline"

# # ---------------- ROUTES ----------------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")

# @app.route("/api/report", methods=["POST"])
# def api_report():
#     data = request.json
#     ip = request.remote_addr
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#     INSERT INTO clients VALUES (%s,%s,%s,%s,%s,%s,%s)
#     ON CONFLICT(client_uuid) DO UPDATE SET
#         mac_address=EXCLUDED.mac_address,
#         hostname=EXCLUDED.hostname,
#         last_seen=EXCLUDED.last_seen,
#         client_ip=EXCLUDED.client_ip,
#         hardware_info=EXCLUDED.hardware_info,
#         installed_apps=EXCLUDED.installed_apps
#     """, (
#         data["uuid"], data["mac"], data["hostname"],
#         data["timestamp"], ip, data["hardware"], data["apps"]
#     ))
#     con.commit()
#     con.close()
#     return jsonify({"status": "ok"})

# @app.route("/api/clients")
# def api_clients():
#     search = request.args.get("search")
#     con = get_db()
#     cur = con.cursor()
#     if search:
#         cur.execute("""
#         SELECT * FROM clients
#         WHERE client_uuid ILIKE %s OR hostname ILIKE %s OR mac_address ILIKE %s
#         """, (f"%{search}%", f"%{search}%", f"%{search}%"))
#     else:
#         cur.execute("SELECT * FROM clients")
#     rows = cur.fetchall()
#     con.close()
#     return jsonify([{
#         "uuid": r[0],
#         "mac": r[1],
#         "hostname": r[2],
#         "last_seen": r[3],
#         "ip": r[4],
#         "status": status_from_last_seen(r[3])
#     } for r in rows])

# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     con.close()
#     if not r:
#         return jsonify({"error": "Client not found"}), 404
#     return jsonify({
#         "uuid": r[0],
#         "mac": r[1],
#         "hostname": r[2],
#         "last_seen": r[3],
#         "ip": r[4],
#         "hardware": safe_json(r[5]),
#         "apps": safe_json(r[6])
#     })

# @app.route("/export/pdf/<uuid>")
# def export_pdf(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     con.close()
#     if not r:
#         return "Client not found", 404

#     fd, path = tempfile.mkstemp(suffix=".pdf")
#     os.close(fd)
#     doc = SimpleDocTemplate(path, pagesize=A4)
#     styles = getSampleStyleSheet()
#     elements = []

#     elements.append(Paragraph("Client Report", styles["Title"]))
#     elements.append(Spacer(1, 12))
#     info = [["Field", "Value"],
#             ["UUID", r[0]], ["MAC", r[1]], ["Hostname", r[2]],
#             ["Last Seen", r[3]], ["IP", r[4]]]
#     t1 = Table(info, colWidths=[120, 350])
#     t1.setStyle(TableStyle([
#         ('GRID', (0,0), (-1,-1), 0.5, colors.black),
#         ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)
#     ]))
#     elements.append(t1)
#     doc.build(elements)
#     return send_file(path, as_attachment=True, mimetype="application/pdf",
#                      download_name=f"{uuid}.pdf")

# @app.route("/export/csv")
# def export_csv():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT client_uuid, mac_address, hostname, last_seen, client_ip FROM clients")
#     rows = cur.fetchall()
#     con.close()

#     def generate():
#         yield "UUID,MAC,Hostname,Last Seen,IP\n"
#         for r in rows:
#             yield f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]}\n"

#     return Response(generate(), mimetype="text/csv",
#                     headers={"Content-Disposition": "attachment;filename=clients.csv"})

# # ---------------- RUN ----------------
# if __name__ == "__main__":
#     init_db()
#     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))










# most reacent 
# import os, json, datetime, psycopg2, tempfile, csv
# from flask import Flask, jsonify, render_template, send_file, request, Response
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors

# DATABASE_URL = os.environ.get("DATABASE_URL")

# app = Flask(__name__, template_folder="templates")

# # ---------------- DATABASE ----------------
# def get_db():
#     return psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=5)

# def init_db():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS clients (
#         client_uuid TEXT PRIMARY KEY,
#         mac_address TEXT,
#         hostname TEXT,
#         last_seen TEXT,
#         client_ip TEXT,
#         hardware_info TEXT,
#         installed_apps TEXT
#     )
#     """)
#     con.commit()
#     con.close()

# # ---------------- HELPERS ----------------
# def safe_json(v):
#     try:
#         return json.loads(v)
#     except:
#         return v

# def status_from_last_seen(ts):
#     try:
#         t = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
#         return "Online" if (datetime.datetime.now() - t).seconds <= 60 else "Offline"
#     except:
#         return "Offline"

# # ---------------- ROUTES ----------------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")

# @app.route("/api/report", methods=["POST"])
# def api_report():
#     data = request.json
#     ip = request.remote_addr

#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#     INSERT INTO clients VALUES (%s,%s,%s,%s,%s,%s,%s)
#     ON CONFLICT(client_uuid) DO UPDATE SET
#         mac_address=EXCLUDED.mac_address,
#         hostname=EXCLUDED.hostname,
#         last_seen=EXCLUDED.last_seen,
#         client_ip=EXCLUDED.client_ip,
#         hardware_info=EXCLUDED.hardware_info,
#         installed_apps=EXCLUDED.installed_apps
#     """, (
#         data["uuid"], data["mac"], data["hostname"],
#         data["timestamp"], ip, data["hardware"], data["apps"]
#     ))
#     con.commit()
#     con.close()
#     return jsonify({"status": "ok"})

# @app.route("/api/clients")
# def api_clients():
#     search = request.args.get("search")
#     con = get_db()
#     cur = con.cursor()
#     if search:
#         cur.execute("""
#         SELECT * FROM clients
#         WHERE client_uuid ILIKE %s OR hostname ILIKE %s OR mac_address ILIKE %s
#         """, (f"%{search}%", f"%{search}%", f"%{search}%"))
#     else:
#         cur.execute("SELECT * FROM clients")
#     rows = cur.fetchall()
#     con.close()
#     return jsonify([{
#         "uuid": r[0],
#         "mac": r[1],
#         "hostname": r[2],
#         "last_seen": r[3],
#         "ip": r[4],
#         "status": status_from_last_seen(r[3])
#     } for r in rows])

# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     con.close()
#     if not r:
#         return jsonify({"error": "Client not found"}), 404
#     return jsonify({
#         "uuid": r[0],
#         "mac": r[1],
#         "hostname": r[2],
#         "last_seen": r[3],
#         "ip": r[4],
#         "hardware": safe_json(r[5]),
#         "apps": safe_json(r[6])
#     })

# @app.route("/export/pdf/<uuid>")
# def export_pdf(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     con.close()
#     if not r:
#         return "Client not found", 404

#     fd, path = tempfile.mkstemp(suffix=".pdf")
#     os.close(fd)

#     doc = SimpleDocTemplate(path, pagesize=A4)
#     styles = getSampleStyleSheet()
#     elements = []

#     elements.append(Paragraph("Client Report", styles["Title"]))
#     elements.append(Spacer(1, 12))

#     # Hardware Table
#     hw = safe_json(r[5])
#     hw_data = [["Field", "Value"]] + [[k, str(v)] for k, v in hw.items()]
#     hw_table = Table(hw_data, colWidths=[120, 350])
#     hw_table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),
#                                   ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
#     elements.append(Paragraph("Hardware Info", styles["Heading2"]))
#     elements.append(hw_table)
#     elements.append(Spacer(1,12))

#     # Installed Apps Table
#     apps = safe_json(r[6])
#     apps_data = [["Installed Apps"]] + [[a] for a in apps]
#     apps_table = Table(apps_data, colWidths=[470])
#     apps_table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),
#                                     ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
#     elements.append(Paragraph("Installed Apps", styles["Heading2"]))
#     elements.append(apps_table)

#     doc.build(elements)
#     return send_file(path, as_attachment=True, mimetype="application/pdf", download_name=f"{uuid}.pdf")

# @app.route("/export/csv")
# def export_csv():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT client_uuid, mac_address, hostname, last_seen, client_ip FROM clients")
#     rows = cur.fetchall()
#     con.close()

#     def generate():
#         yield "UUID,MAC,Hostname,Last Seen,IP\n"
#         for r in rows:
#             yield f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]}\n"

#     return Response(generate(), mimetype="text/csv",
#                     headers={"Content-Disposition": "attachment;filename=clients.csv"})

# # ---------------- RUN ----------------
# if __name__ == "__main__":
#     init_db()
#     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))












# import os, json, datetime, psycopg2, tempfile
# from flask import Flask, jsonify, render_template, send_file, request, Response
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors

# DATABASE_URL = os.environ.get("DATABASE_URL")

# app = Flask(__name__, template_folder="templates")

# # ---------- DB ----------
# def get_db():
#     return psycopg2.connect(DATABASE_URL, sslmode="require")

# def init_db():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS clients (
#         uuid TEXT PRIMARY KEY,
#         mac TEXT,
#         hostname TEXT,
#         ip TEXT,
#         last_seen TIMESTAMP,
#         hardware_info TEXT,
#         installed_apps TEXT
#     )
#     """)
#     con.commit()
#     con.close()

# def safe_json(v):
#     try:
#         return json.loads(v)
#     except:
#         return []

# def parse_ts(ts):
#     if isinstance(ts, datetime.datetime):
#         return ts
#     try:
#         return datetime.datetime.fromisoformat(str(ts))
#     except:
#         return datetime.datetime.utcnow()

# # ---------- ROUTES ----------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")

# @app.route("/api/report", methods=["POST"])
# def api_report():
#     data = request.get_json(force=True)
#     ip = request.remote_addr
#     now = datetime.datetime.utcnow()

#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#     INSERT INTO clients (uuid, mac, hostname, ip, last_seen, hardware_info, installed_apps)
#     VALUES (%s,%s,%s,%s,%s,%s,%s)
#     ON CONFLICT(uuid) DO UPDATE SET
#         mac=EXCLUDED.mac,
#         hostname=EXCLUDED.hostname,
#         ip=EXCLUDED.ip,
#         last_seen=EXCLUDED.last_seen,
#         hardware_info=EXCLUDED.hardware_info,
#         installed_apps=EXCLUDED.installed_apps
#     """, (
#         data["uuid"],
#         data["mac"],
#         data["hostname"],
#         ip,
#         now,
#         data["hardware"],
#         data["apps"]
#     ))
#     con.commit()
#     con.close()

#     return jsonify({"status": "ok"})

# @app.route("/api/clients")
# def api_clients():
#     search = request.args.get("search","")
#     con = get_db()
#     cur = con.cursor()

#     if search:
#         cur.execute("""
#         SELECT uuid, mac, hostname, ip, last_seen
#         FROM clients
#         WHERE uuid ILIKE %s OR hostname ILIKE %s OR mac ILIKE %s
#         ORDER BY last_seen DESC
#         """,(f"%{search}%",f"%{search}%",f"%{search}%"))
#     else:
#         cur.execute("SELECT uuid, mac, hostname, ip, last_seen FROM clients ORDER BY last_seen DESC")

#     rows = cur.fetchall()
#     con.close()

#     now = datetime.datetime.utcnow()
#     out = []
#     for r in rows:
#         ts = parse_ts(r[4])
#         status = "Online" if (now-ts).total_seconds() < 60 else "Offline"
#         out.append({
#             "uuid": r[0],
#             "mac": r[1],
#             "hostname": r[2],
#             "ip": r[3],
#             "last_seen": ts.strftime("%Y-%m-%d %H:%M:%S"),
#             "status": status
#         })
#     return jsonify(out)

# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE uuid=%s",(uuid,))
#     r = cur.fetchone()
#     con.close()

#     if not r:
#         return jsonify({"error":"Client not found"}),404

#     return jsonify({
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "ip":r[3],
#         "last_seen":parse_ts(r[4]).strftime("%Y-%m-%d %H:%M:%S"),
#         "hardware":safe_json(r[5]),
#         "apps":safe_json(r[6])
#     })

# # ---------- RUN ----------
# if __name__ == "__main__":
#     init_db()
#     app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))









import os, json, datetime, psycopg2, tempfile
from flask import Flask, jsonify, render_template, send_file, request, Response
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

DATABASE_URL = os.environ.get("DATABASE_URL")

app = Flask(__name__, template_folder="templates")

# ---------------- DATABASE ----------------
def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=5)

def init_db():
    con = get_db()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        client_uuid TEXT PRIMARY KEY,
        mac_address TEXT,
        hostname TEXT,
        last_seen TEXT,
        client_ip TEXT,
        hardware_info TEXT,
        installed_apps TEXT
    )
    """)
    con.commit()
    con.close()

# ---------------- HELPERS ----------------
def safe_json(v):
    if not v:
        return []
    try:
        return json.loads(v)
    except:
        return []

def status_from_last_seen(ts):
    try:
        t = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        return "Online" if (datetime.datetime.now() - t).total_seconds() <= 60 else "Offline"
    except:
        return "Offline"

def merge_app_history(old_apps, new_apps):
    old_dict = {a["name"]: a for a in old_apps}
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for app in new_apps:
        name = app.get("name")
        version = app.get("version")

        if name in old_dict:
            old_version = old_dict[name].get("version")
            history = old_dict[name].get("history", [])

            if old_version != version:
                history.append(f"Updated from {old_version} to {version} on {now}")
            app["history"] = history
        else:
            app["history"] = [f"Installed on {now}"]

    return new_apps

# ---------------- ROUTES ----------------
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/report", methods=["POST"])
def api_report():
    data = request.json
    ip = request.remote_addr

    con = get_db()
    cur = con.cursor()

    cur.execute("SELECT installed_apps FROM clients WHERE client_uuid=%s", (data["uuid"],))
    existing = cur.fetchone()

    old_apps = safe_json(existing[0]) if existing else []
    new_apps = safe_json(data["apps"])

    merged_apps = merge_app_history(old_apps, new_apps)

    cur.execute("""
    INSERT INTO clients VALUES (%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT(client_uuid) DO UPDATE SET
        mac_address=EXCLUDED.mac_address,
        hostname=EXCLUDED.hostname,
        last_seen=EXCLUDED.last_seen,
        client_ip=EXCLUDED.client_ip,
        hardware_info=EXCLUDED.hardware_info,
        installed_apps=EXCLUDED.installed_apps
    """, (
        data["uuid"],
        data["mac"],
        data["hostname"],
        data["timestamp"],
        ip,
        data["hardware"],
        json.dumps(merged_apps)
    ))

    con.commit()
    con.close()

    return jsonify({"status": "ok"})

@app.route("/api/clients")
def api_clients():
    search = request.args.get("search")
    con = get_db()
    cur = con.cursor()

    if search:
        cur.execute("""
        SELECT * FROM clients
        WHERE client_uuid ILIKE %s OR hostname ILIKE %s OR mac_address ILIKE %s
        """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cur.execute("SELECT * FROM clients")

    rows = cur.fetchall()
    con.close()

    return jsonify([{
        "uuid": r[0],
        "mac": r[1],
        "hostname": r[2],
        "last_seen": r[3],
        "ip": r[4],
        "status": status_from_last_seen(r[3])
    } for r in rows])

@app.route("/api/client/<uuid>")
def api_client(uuid):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
    r = cur.fetchone()
    con.close()

    if not r:
        return jsonify({"error": "Client not found"}), 404

    return jsonify({
        "uuid": r[0],
        "mac": r[1],
        "hostname": r[2],
        "last_seen": r[3],
        "ip": r[4],
        "hardware": safe_json(r[5]),
        "apps": safe_json(r[6])
    })

# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
