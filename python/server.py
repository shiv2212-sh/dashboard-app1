# # import threading, socket, sqlite3, json, io, csv, datetime, os, tempfile
# # from flask import Flask, jsonify, render_template, send_file, request
# # from waitress import serve
# # from reportlab.lib.pagesizes import A4
# # from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# # from reportlab.lib.styles import getSampleStyleSheet
# # from reportlab.lib import colors
# # import os
# # from waitress import serve
# # import psutil



# # DB_FILE = r"C:\Users\shivs\PyCharmMiscProject\client-dashboard-app\python\server_data.db"
# # TEMPLATE_DIR = os.path.join(os.path.dirname(DB_FILE), "templates")

# # TCP_HOST = "0.0.0.0"
# # TCP_PORT = 9002

# # app = Flask(__name__, template_folder=TEMPLATE_DIR)
# # shutdown_flag = threading.Event()

# # # ---------------- DATABASE ----------------
# # def init_db():
# #     os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
# #     con = sqlite3.connect(DB_FILE)
# #     cur = con.cursor()

# #     cur.execute("""
# #     CREATE TABLE IF NOT EXISTS clients (
# #         client_uuid TEXT PRIMARY KEY,
# #         mac_address TEXT,
# #         hostname TEXT,
# #         last_seen TEXT,
# #         client_ip TEXT,
# #         hardware_info TEXT,
# #         installed_apps TEXT
# #     )""")

# #     cur.execute("""
# #     CREATE TABLE IF NOT EXISTS app_history (
# #         client_uuid TEXT,
# #         app_name TEXT,
# #         version TEXT,
# #         status TEXT,
# #         time TEXT
# #     )""")

# #     con.commit()
# #     con.close()


# # def upsert_client(data, ip):
# #     con = sqlite3.connect(DB_FILE)
# #     cur = con.cursor()

# #     cur.execute("""
# #     INSERT INTO clients VALUES (?, ?, ?, ?, ?, ?, ?)
# #     ON CONFLICT(client_uuid) DO UPDATE SET
# #         mac_address=excluded.mac_address,
# #         hostname=excluded.hostname,
# #         last_seen=excluded.last_seen,
# #         client_ip=excluded.client_ip,
# #         hardware_info=excluded.hardware_info,
# #         installed_apps=excluded.installed_apps
# #     """, (data["uuid"], data["mac"], data["hostname"],
# #           data["timestamp"], ip, data["hardware"], data["apps"]))

# #     for line in data["apps"].splitlines():
# #         if "|" in line:
# #             name, version, install_date, _ = line.split("|", 3)
# #             time_val = install_date if install_date != "-" else data["timestamp"]
# #             cur.execute("INSERT INTO app_history VALUES (?,?,?,?,?)",
# #                         (data["uuid"], name, version, "Installed", time_val))

# #     con.commit()
# #     con.close()


# # # ---------------- TCP SERVER ----------------
# # def recv_line(sock):
# #     data = b""
# #     while not data.endswith(b"\n"):
# #         p = sock.recv(1)
# #         if not p: return None
# #         data += p
# #     return data.decode().strip()


# # def recv_exact(sock, n):
# #     data = b""
# #     while len(data) < n:
# #         p = sock.recv(n - len(data))
# #         if not p: return None
# #         data += p
# #     return data


# # def recv_text(sock):
# #     l = recv_line(sock)
# #     if not l: return None
# #     payload = recv_exact(sock, int(l))
# #     return payload.decode() if payload else None


# # def parse_text_data(text):
# #     lines = text.splitlines()
# #     data = {"hardware": "", "apps": ""}
# #     mode = None
# #     for line in lines:
# #         if line.startswith("CLIENT_UUID:"): data["uuid"] = line.split(":",1)[1].strip()
# #         elif line.startswith("MAC_ADDRESS:"): data["mac"] = line.split(":",1)[1].strip()
# #         elif line.startswith("HOSTNAME:"): data["hostname"] = line.split(":",1)[1].strip()
# #         elif line.startswith("TIMESTAMP:"): data["timestamp"] = line.split(":",1)[1].strip()
# #         elif line.startswith("=== HARDWARE"): mode="hw"
# #         elif line.startswith("=== APPLICATIONS"): mode="apps"
# #         elif mode=="hw": data["hardware"] += line + "\n"
# #         elif mode=="apps": data["apps"] += line + "\n"
# #     return data


# # def handle_client(sock, addr):
# #     ip,_ = addr
# #     cmd = recv_line(sock)
# #     if cmd != "get apps":
# #         sock.close()
# #         return
# #     text = recv_text(sock)
# #     data = parse_text_data(text)
# #     if "uuid" in data:
# #         upsert_client(data, ip)
# #     sock.sendall(b"OK\n")
# #     sock.close()


# # def tcp_server():
# #     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# #     s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# #     s.bind((TCP_HOST, TCP_PORT))
# #     s.listen(5)
# #     print(f"[+] TCP listening {TCP_HOST}:{TCP_PORT}")
# #     while not shutdown_flag.is_set():
# #         try:
# #             s.settimeout(1)
# #             c,addr = s.accept()
# #             threading.Thread(target=handle_client, args=(c,addr), daemon=True).start()
# #         except socket.timeout:
# #             continue
# #     s.close()


# # # ---------------- HELPERS ----------------
# # def safe_json(v):
# #     try:
# #         return json.loads(v)
# #     except:
# #         return v.splitlines()


# # def status_from_last_seen(ts):
# #     try:
# #         t = datetime.datetime.strptime(ts,"%Y-%m-%d %H:%M:%S")
# #         return "Online" if (datetime.datetime.now()-t).seconds<=60 else "Offline"
# #     except:
# #         return "Offline"


# # # ---------------- FLASK ROUTES ----------------
# # @app.route("/")
# # def dashboard():
# #     return render_template("dashboard.html")


# # @app.route("/api/clients")
# # def api_clients():
# #     con = sqlite3.connect(DB_FILE)
# #     cur = con.cursor()
# #     cur.execute("SELECT * FROM clients")
# #     rows = cur.fetchall()
# #     con.close()

# #     return jsonify([{
# #         "uuid":r[0],
# #         "mac":r[1],
# #         "hostname":r[2],
# #         "last_seen":r[3],
# #         "ip":r[4],
# #         "status":status_from_last_seen(r[3])
# #     } for r in rows])


# # @app.route("/api/client/<uuid>")
# # def api_client(uuid):
# #     con = sqlite3.connect(DB_FILE)
# #     cur = con.cursor()
# #     cur.execute("SELECT * FROM clients WHERE client_uuid=?", (uuid,))
# #     r = cur.fetchone()
# #     con.close()

# #     return jsonify({
# #         "uuid":r[0],
# #         "mac":r[1],
# #         "hostname":r[2],
# #         "last_seen":r[3],
# #         "ip":r[4],
# #         "hardware":safe_json(r[5]),
# #         "apps":safe_json(r[6])
# #     })


# # @app.route("/export/pdf/<uuid>")
# # def export_pdf(uuid):
# #     con = sqlite3.connect(DB_FILE)
# #     cur = con.cursor()
# #     cur.execute("SELECT * FROM clients WHERE client_uuid=?", (uuid,))
# #     r = cur.fetchone()
# #     con.close()

# #     if not r:
# #         return "Client not found", 404

# #     fd, path = tempfile.mkstemp(suffix=".pdf")
# #     os.close(fd)

# #     doc = SimpleDocTemplate(path, pagesize=A4)
# #     styles = getSampleStyleSheet()
# #     elements = []

# #     elements.append(Paragraph("Client Report", styles["Title"]))
# #     elements.append(Spacer(1, 12))

# #     info = [["Field","Value"],
# #             ["UUID",r[0]],["MAC",r[1]],["Hostname",r[2]],
# #             ["Last Seen",r[3]],["IP",r[4]]]

# #     t1 = Table(info, colWidths=[120,350])
# #     t1.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),
# #                             ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
# #     elements.append(t1); elements.append(Spacer(1,20))

# #     elements.append(Paragraph("Hardware", styles["Heading2"]))
# #     hw = [["Component"]] + [[l] for l in safe_json(r[5])]
# #     t2 = Table(hw, colWidths=[470])
# #     t2.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black)]))
# #     elements.append(t2); elements.append(Spacer(1,20))

# #     elements.append(Paragraph("Applications", styles["Heading2"]))
# #     apps = [["Name","Version","Date","Size"]]
# #     for l in safe_json(r[6]):
# #         if "|" in l: apps.append(l.split("|",3))
# #     t3 = Table(apps, colWidths=[180,90,100,100])
# #     t3.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),
# #                             ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
# #     elements.append(t3)

# #     doc.build(elements)

# #     return send_file(path, as_attachment=True,
# #                      mimetype="application/pdf",
# #                      download_name=f"{uuid}.pdf")


# # @app.route("/shutdown", methods=["POST"])
# # def shutdown():
# #     shutdown_flag.set()
# #     os._exit(0)


# # # ---------------- RUN ----------------

# # if __name__ == "__main__":
# #     port = int(os.environ.get("PORT", 9001))
# #     serve(app, host="0.0.0.0", port=port)







# # from flask import Flask, jsonify, render_template, request, send_file, Response
# # import os, json, datetime, psycopg2, tempfile, csv
# # from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# # from reportlab.lib.pagesizes import A4
# # from reportlab.lib.styles import getSampleStyleSheet
# # from reportlab.lib import colors

# # DATABASE_URL = os.environ.get("DATABASE_URL")

# # app = Flask(__name__, template_folder="templates")

# # # ---------------- DATABASE ----------------
# # def get_db():
# #     return psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=5)

# # def init_db():
# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("""
# #     CREATE TABLE IF NOT EXISTS clients (
# #         client_uuid TEXT PRIMARY KEY,
# #         mac_address TEXT,
# #         hostname TEXT,
# #         last_seen TEXT,
# #         client_ip TEXT,
# #         hardware_info TEXT,
# #         installed_apps TEXT
# #     )
# #     """)
# #     con.commit()
# #     con.close()

# # # ---------------- HELPERS ----------------
# # def safe_json(v):
# #     try:
# #         return json.loads(v)
# #     except:
# #         return v

# # def status_from_last_seen(ts):
# #     try:
# #         t = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
# #         return "Online" if (datetime.datetime.now() - t).seconds <= 60 else "Offline"
# #     except:
# #         return "Offline"

# # # ---------------- ROUTES ----------------
# # @app.route("/")
# # def dashboard():
# #     return render_template("dashboard.html")

# # @app.route("/api/report", methods=["POST"])
# # def api_report():
# #     data = request.json
# #     ip = request.remote_addr
# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("""
# #     INSERT INTO clients VALUES (%s,%s,%s,%s,%s,%s,%s)
# #     ON CONFLICT(client_uuid) DO UPDATE SET
# #         mac_address=EXCLUDED.mac_address,
# #         hostname=EXCLUDED.hostname,
# #         last_seen=EXCLUDED.last_seen,
# #         client_ip=EXCLUDED.client_ip,
# #         hardware_info=EXCLUDED.hardware_info,
# #         installed_apps=EXCLUDED.installed_apps
# #     """, (
# #         data["uuid"], data["mac"], data["hostname"],
# #         data["timestamp"], ip, data["hardware"], data["apps"]
# #     ))
# #     con.commit()
# #     con.close()
# #     return jsonify({"status": "ok"})

# # @app.route("/api/clients")
# # def api_clients():
# #     search = request.args.get("search")
# #     con = get_db()
# #     cur = con.cursor()
# #     if search:
# #         cur.execute("""
# #         SELECT * FROM clients
# #         WHERE client_uuid ILIKE %s OR hostname ILIKE %s OR mac_address ILIKE %s
# #         """, (f"%{search}%", f"%{search}%", f"%{search}%"))
# #     else:
# #         cur.execute("SELECT * FROM clients")
# #     rows = cur.fetchall()
# #     con.close()
# #     return jsonify([{
# #         "uuid": r[0],
# #         "mac": r[1],
# #         "hostname": r[2],
# #         "last_seen": r[3],
# #         "ip": r[4],
# #         "status": status_from_last_seen(r[3])
# #     } for r in rows])

# # @app.route("/api/client/<uuid>")
# # def api_client(uuid):
# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
# #     r = cur.fetchone()
# #     con.close()
# #     if not r:
# #         return jsonify({"error": "Client not found"}), 404
# #     return jsonify({
# #         "uuid": r[0],
# #         "mac": r[1],
# #         "hostname": r[2],
# #         "last_seen": r[3],
# #         "ip": r[4],
# #         "hardware": safe_json(r[5]),
# #         "apps": safe_json(r[6])
# #     })

# # @app.route("/export/pdf/<uuid>")
# # def export_pdf(uuid):
# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
# #     r = cur.fetchone()
# #     con.close()
# #     if not r:
# #         return "Client not found", 404

# #     fd, path = tempfile.mkstemp(suffix=".pdf")
# #     os.close(fd)
# #     doc = SimpleDocTemplate(path, pagesize=A4)
# #     styles = getSampleStyleSheet()
# #     elements = []

# #     elements.append(Paragraph("Client Report", styles["Title"]))
# #     elements.append(Spacer(1, 12))
# #     info = [["Field", "Value"],
# #             ["UUID", r[0]], ["MAC", r[1]], ["Hostname", r[2]],
# #             ["Last Seen", r[3]], ["IP", r[4]]]
# #     t1 = Table(info, colWidths=[120, 350])
# #     t1.setStyle(TableStyle([
# #         ('GRID', (0,0), (-1,-1), 0.5, colors.black),
# #         ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)
# #     ]))
# #     elements.append(t1)
# #     doc.build(elements)
# #     return send_file(path, as_attachment=True, mimetype="application/pdf",
# #                      download_name=f"{uuid}.pdf")

# # @app.route("/export/csv")
# # def export_csv():
# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("SELECT client_uuid, mac_address, hostname, last_seen, client_ip FROM clients")
# #     rows = cur.fetchall()
# #     con.close()

# #     def generate():
# #         yield "UUID,MAC,Hostname,Last Seen,IP\n"
# #         for r in rows:
# #             yield f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]}\n"

# #     return Response(generate(), mimetype="text/csv",
# #                     headers={"Content-Disposition": "attachment;filename=clients.csv"})

# # # ---------------- RUN ----------------
# # if __name__ == "__main__":
# #     init_db()
# #     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))










# # most reacent 
# # import os, json, datetime, psycopg2, tempfile, csv
# # from flask import Flask, jsonify, render_template, send_file, request, Response
# # from reportlab.lib.pagesizes import A4
# # from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# # from reportlab.lib.styles import getSampleStyleSheet
# # from reportlab.lib import colors

# # DATABASE_URL = os.environ.get("DATABASE_URL")

# # app = Flask(__name__, template_folder="templates")

# # # ---------------- DATABASE ----------------
# # def get_db():
# #     return psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=5)

# # def init_db():
# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("""
# #     CREATE TABLE IF NOT EXISTS clients (
# #         client_uuid TEXT PRIMARY KEY,
# #         mac_address TEXT,
# #         hostname TEXT,
# #         last_seen TEXT,
# #         client_ip TEXT,
# #         hardware_info TEXT,
# #         installed_apps TEXT
# #     )
# #     """)
# #     con.commit()
# #     con.close()

# # # ---------------- HELPERS ----------------
# # def safe_json(v):
# #     try:
# #         return json.loads(v)
# #     except:
# #         return v

# # def status_from_last_seen(ts):
# #     try:
# #         t = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
# #         return "Online" if (datetime.datetime.now() - t).seconds <= 60 else "Offline"
# #     except:
# #         return "Offline"

# # # ---------------- ROUTES ----------------
# # @app.route("/")
# # def dashboard():
# #     return render_template("dashboard.html")

# # @app.route("/api/report", methods=["POST"])
# # def api_report():
# #     data = request.json
# #     ip = request.remote_addr

# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("""
# #     INSERT INTO clients VALUES (%s,%s,%s,%s,%s,%s,%s)
# #     ON CONFLICT(client_uuid) DO UPDATE SET
# #         mac_address=EXCLUDED.mac_address,
# #         hostname=EXCLUDED.hostname,
# #         last_seen=EXCLUDED.last_seen,
# #         client_ip=EXCLUDED.client_ip,
# #         hardware_info=EXCLUDED.hardware_info,
# #         installed_apps=EXCLUDED.installed_apps
# #     """, (
# #         data["uuid"], data["mac"], data["hostname"],
# #         data["timestamp"], ip, data["hardware"], data["apps"]
# #     ))
# #     con.commit()
# #     con.close()
# #     return jsonify({"status": "ok"})

# # @app.route("/api/clients")
# # def api_clients():
# #     search = request.args.get("search")
# #     con = get_db()
# #     cur = con.cursor()
# #     if search:
# #         cur.execute("""
# #         SELECT * FROM clients
# #         WHERE client_uuid ILIKE %s OR hostname ILIKE %s OR mac_address ILIKE %s
# #         """, (f"%{search}%", f"%{search}%", f"%{search}%"))
# #     else:
# #         cur.execute("SELECT * FROM clients")
# #     rows = cur.fetchall()
# #     con.close()
# #     return jsonify([{
# #         "uuid": r[0],
# #         "mac": r[1],
# #         "hostname": r[2],
# #         "last_seen": r[3],
# #         "ip": r[4],
# #         "status": status_from_last_seen(r[3])
# #     } for r in rows])

# # @app.route("/api/client/<uuid>")
# # def api_client(uuid):
# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
# #     r = cur.fetchone()
# #     con.close()
# #     if not r:
# #         return jsonify({"error": "Client not found"}), 404
# #     return jsonify({
# #         "uuid": r[0],
# #         "mac": r[1],
# #         "hostname": r[2],
# #         "last_seen": r[3],
# #         "ip": r[4],
# #         "hardware": safe_json(r[5]),
# #         "apps": safe_json(r[6])
# #     })

# # @app.route("/export/pdf/<uuid>")
# # def export_pdf(uuid):
# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
# #     r = cur.fetchone()
# #     con.close()
# #     if not r:
# #         return "Client not found", 404

# #     fd, path = tempfile.mkstemp(suffix=".pdf")
# #     os.close(fd)

# #     doc = SimpleDocTemplate(path, pagesize=A4)
# #     styles = getSampleStyleSheet()
# #     elements = []

# #     elements.append(Paragraph("Client Report", styles["Title"]))
# #     elements.append(Spacer(1, 12))

# #     # Hardware Table
# #     hw = safe_json(r[5])
# #     hw_data = [["Field", "Value"]] + [[k, str(v)] for k, v in hw.items()]
# #     hw_table = Table(hw_data, colWidths=[120, 350])
# #     hw_table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),
# #                                   ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
# #     elements.append(Paragraph("Hardware Info", styles["Heading2"]))
# #     elements.append(hw_table)
# #     elements.append(Spacer(1,12))

# #     # Installed Apps Table
# #     apps = safe_json(r[6])
# #     apps_data = [["Installed Apps"]] + [[a] for a in apps]
# #     apps_table = Table(apps_data, colWidths=[470])
# #     apps_table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),
# #                                     ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
# #     elements.append(Paragraph("Installed Apps", styles["Heading2"]))
# #     elements.append(apps_table)

# #     doc.build(elements)
# #     return send_file(path, as_attachment=True, mimetype="application/pdf", download_name=f"{uuid}.pdf")

# # @app.route("/export/csv")
# # def export_csv():
# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("SELECT client_uuid, mac_address, hostname, last_seen, client_ip FROM clients")
# #     rows = cur.fetchall()
# #     con.close()

# #     def generate():
# #         yield "UUID,MAC,Hostname,Last Seen,IP\n"
# #         for r in rows:
# #             yield f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]}\n"

# #     return Response(generate(), mimetype="text/csv",
# #                     headers={"Content-Disposition": "attachment;filename=clients.csv"})

# # # ---------------- RUN ----------------
# # if __name__ == "__main__":
# #     init_db()
# #     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))












# # import os, json, datetime, psycopg2, tempfile
# # from flask import Flask, jsonify, render_template, send_file, request, Response
# # from reportlab.lib.pagesizes import A4
# # from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# # from reportlab.lib.styles import getSampleStyleSheet
# # from reportlab.lib import colors

# # DATABASE_URL = os.environ.get("DATABASE_URL")

# # app = Flask(__name__, template_folder="templates")

# # # ---------- DB ----------
# # def get_db():
# #     return psycopg2.connect(DATABASE_URL, sslmode="require")

# # def init_db():
# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("""
# #     CREATE TABLE IF NOT EXISTS clients (
# #         uuid TEXT PRIMARY KEY,
# #         mac TEXT,
# #         hostname TEXT,
# #         ip TEXT,
# #         last_seen TIMESTAMP,
# #         hardware_info TEXT,
# #         installed_apps TEXT
# #     )
# #     """)
# #     con.commit()
# #     con.close()

# # def safe_json(v):
# #     try:
# #         return json.loads(v)
# #     except:
# #         return []

# # def parse_ts(ts):
# #     if isinstance(ts, datetime.datetime):
# #         return ts
# #     try:
# #         return datetime.datetime.fromisoformat(str(ts))
# #     except:
# #         return datetime.datetime.utcnow()

# # # ---------- ROUTES ----------
# # @app.route("/")
# # def dashboard():
# #     return render_template("dashboard.html")

# # @app.route("/api/report", methods=["POST"])
# # def api_report():
# #     data = request.get_json(force=True)
# #     ip = request.remote_addr
# #     now = datetime.datetime.utcnow()

# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("""
# #     INSERT INTO clients (uuid, mac, hostname, ip, last_seen, hardware_info, installed_apps)
# #     VALUES (%s,%s,%s,%s,%s,%s,%s)
# #     ON CONFLICT(uuid) DO UPDATE SET
# #         mac=EXCLUDED.mac,
# #         hostname=EXCLUDED.hostname,
# #         ip=EXCLUDED.ip,
# #         last_seen=EXCLUDED.last_seen,
# #         hardware_info=EXCLUDED.hardware_info,
# #         installed_apps=EXCLUDED.installed_apps
# #     """, (
# #         data["uuid"],
# #         data["mac"],
# #         data["hostname"],
# #         ip,
# #         now,
# #         data["hardware"],
# #         data["apps"]
# #     ))
# #     con.commit()
# #     con.close()

# #     return jsonify({"status": "ok"})

# # @app.route("/api/clients")
# # def api_clients():
# #     search = request.args.get("search","")
# #     con = get_db()
# #     cur = con.cursor()

# #     if search:
# #         cur.execute("""
# #         SELECT uuid, mac, hostname, ip, last_seen
# #         FROM clients
# #         WHERE uuid ILIKE %s OR hostname ILIKE %s OR mac ILIKE %s
# #         ORDER BY last_seen DESC
# #         """,(f"%{search}%",f"%{search}%",f"%{search}%"))
# #     else:
# #         cur.execute("SELECT uuid, mac, hostname, ip, last_seen FROM clients ORDER BY last_seen DESC")

# #     rows = cur.fetchall()
# #     con.close()

# #     now = datetime.datetime.utcnow()
# #     out = []
# #     for r in rows:
# #         ts = parse_ts(r[4])
# #         status = "Online" if (now-ts).total_seconds() < 60 else "Offline"
# #         out.append({
# #             "uuid": r[0],
# #             "mac": r[1],
# #             "hostname": r[2],
# #             "ip": r[3],
# #             "last_seen": ts.strftime("%Y-%m-%d %H:%M:%S"),
# #             "status": status
# #         })
# #     return jsonify(out)

# # @app.route("/api/client/<uuid>")
# # def api_client(uuid):
# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("SELECT * FROM clients WHERE uuid=%s",(uuid,))
# #     r = cur.fetchone()
# #     con.close()

# #     if not r:
# #         return jsonify({"error":"Client not found"}),404

# #     return jsonify({
# #         "uuid":r[0],
# #         "mac":r[1],
# #         "hostname":r[2],
# #         "ip":r[3],
# #         "last_seen":parse_ts(r[4]).strftime("%Y-%m-%d %H:%M:%S"),
# #         "hardware":safe_json(r[5]),
# #         "apps":safe_json(r[6])
# #     })

# # # ---------- RUN ----------
# # if __name__ == "__main__":
# #     init_db()
# #     app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))









# # import os, json, datetime, psycopg2, tempfile
# # from flask import Flask, jsonify, render_template, send_file, request, Response
# # from reportlab.lib.pagesizes import A4
# # from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# # from reportlab.lib.styles import getSampleStyleSheet
# # from reportlab.lib import colors

# # DATABASE_URL = os.environ.get("DATABASE_URL")

# # app = Flask(__name__, template_folder="templates")

# # # ---------------- DATABASE ----------------
# # def get_db():
# #     return psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=5)

# # def init_db():
# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("""
# #     CREATE TABLE IF NOT EXISTS clients (
# #         client_uuid TEXT PRIMARY KEY,
# #         mac_address TEXT,
# #         hostname TEXT,
# #         last_seen TEXT,
# #         client_ip TEXT,
# #         hardware_info TEXT,
# #         installed_apps TEXT
# #     )
# #     """)
# #     con.commit()
# #     con.close()

# # # ---------------- HELPERS ----------------
# # def safe_json(v):
# #     if not v:
# #         return []
# #     try:
# #         return json.loads(v)
# #     except:
# #         return []

# # def status_from_last_seen(ts):
# #     try:
# #         t = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
# #         return "Online" if (datetime.datetime.now() - t).total_seconds() <= 60 else "Offline"
# #     except:
# #         return "Offline"

# # def merge_app_history(old_apps, new_apps):
# #     old_dict = {a["name"]: a for a in old_apps}
# #     now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# #     for app in new_apps:
# #         name = app.get("name")
# #         version = app.get("version")

# #         if name in old_dict:
# #             old_version = old_dict[name].get("version")
# #             history = old_dict[name].get("history", [])

# #             if old_version != version:
# #                 history.append(f"Updated from {old_version} to {version} on {now}")
# #             app["history"] = history
# #         else:
# #             app["history"] = [f"Installed on {now}"]

# #     return new_apps

# # # ---------------- ROUTES ----------------
# # @app.route("/")
# # def dashboard():
# #     return render_template("dashboard.html")

# # @app.route("/api/report", methods=["POST"])
# # def api_report():
# #     data = request.json
# #     ip = request.remote_addr

# #     con = get_db()
# #     cur = con.cursor()

# #     cur.execute("SELECT installed_apps FROM clients WHERE client_uuid=%s", (data["uuid"],))
# #     existing = cur.fetchone()

# #     old_apps = safe_json(existing[0]) if existing else []
# #     new_apps = safe_json(data["apps"])

# #     merged_apps = merge_app_history(old_apps, new_apps)

# #     cur.execute("""
# #     INSERT INTO clients VALUES (%s,%s,%s,%s,%s,%s,%s)
# #     ON CONFLICT(client_uuid) DO UPDATE SET
# #         mac_address=EXCLUDED.mac_address,
# #         hostname=EXCLUDED.hostname,
# #         last_seen=EXCLUDED.last_seen,
# #         client_ip=EXCLUDED.client_ip,
# #         hardware_info=EXCLUDED.hardware_info,
# #         installed_apps=EXCLUDED.installed_apps
# #     """, (
# #         data["uuid"],
# #         data["mac"],
# #         data["hostname"],
# #         data["timestamp"],
# #         ip,
# #         data["hardware"],
# #         json.dumps(merged_apps)
# #     ))

# #     con.commit()
# #     con.close()

# #     return jsonify({"status": "ok"})

# # @app.route("/api/clients")
# # def api_clients():
# #     search = request.args.get("search")
# #     con = get_db()
# #     cur = con.cursor()

# #     if search:
# #         cur.execute("""
# #         SELECT * FROM clients
# #         WHERE client_uuid ILIKE %s OR hostname ILIKE %s OR mac_address ILIKE %s
# #         """, (f"%{search}%", f"%{search}%", f"%{search}%"))
# #     else:
# #         cur.execute("SELECT * FROM clients")

# #     rows = cur.fetchall()
# #     con.close()

# #     return jsonify([{
# #         "uuid": r[0],
# #         "mac": r[1],
# #         "hostname": r[2],
# #         "last_seen": r[3],
# #         "ip": r[4],
# #         "status": status_from_last_seen(r[3])
# #     } for r in rows])

# # @app.route("/api/client/<uuid>")
# # def api_client(uuid):
# #     con = get_db()
# #     cur = con.cursor()
# #     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
# #     r = cur.fetchone()
# #     con.close()

# #     if not r:
# #         return jsonify({"error": "Client not found"}), 404

# #     return jsonify({
# #         "uuid": r[0],
# #         "mac": r[1],
# #         "hostname": r[2],
# #         "last_seen": r[3],
# #         "ip": r[4],
# #         "hardware": safe_json(r[5]),
# #         "apps": safe_json(r[6])
# #     })

# # # ---------------- RUN ----------------
# # if __name__ == "__main__":
# #     init_db()
# #     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))















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












# from flask import Flask, request, jsonify, send_file
# import psycopg2, psycopg2.extras
# import json, datetime, io, os

# # Get database URL from environment variable
# DATABASE_URL = os.environ.get("DATABASE_URL")
# if not DATABASE_URL:
#     raise ValueError("DATABASE_URL environment variable is not set!")

# app = Flask(__name__, template_folder="templates")


# def get_db():
#     """Get a new database connection."""
#     return psycopg2.connect(DATABASE_URL, sslmode="require")


# def init_db():
#     """Initialize the database table."""
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS clients (
#             client_uuid TEXT PRIMARY KEY,
#             mac TEXT,
#             hostname TEXT,
#             last_seen TIMESTAMP,
#             ip TEXT,
#             hardware JSONB,
#             apps JSONB
#         )
#     """)
#     con.commit()
#     cur.close()
#     con.close()


# @app.route("/api/report", methods=["POST"])
# def api_report():
#     """Receive client report and store/update in database."""
#     data = request.get_json()
#     ip = request.remote_addr

#     if not data:
#         return jsonify({"error": "No JSON received"}), 400

#     # Ensure required fields are present
#     required = ["uuid", "mac", "hostname", "timestamp", "hardware", "apps"]
#     for r in required:
#         if r not in data:
#             return jsonify({"error": f"Missing {r}"}), 400

#     # Insert or update client in DB
#     con = get_db()
#     cur = con.cursor()
#     try:
#         cur.execute("""
#             INSERT INTO clients (client_uuid, mac, hostname, last_seen, ip, hardware, apps)
#             VALUES (%s,%s,%s,%s,%s,%s,%s)
#             ON CONFLICT (client_uuid) DO UPDATE SET
#                 mac=EXCLUDED.mac,
#                 hostname=EXCLUDED.hostname,
#                 last_seen=EXCLUDED.last_seen,
#                 ip=EXCLUDED.ip,
#                 hardware=EXCLUDED.hardware,
#                 apps=EXCLUDED.apps
#         """, (
#             data["uuid"],
#             data["mac"],
#             data["hostname"],
#             data["timestamp"],
#             ip,
#             json.dumps(data["hardware"]),  # convert dict → JSON
#             json.dumps(data["apps"])       # convert list/dict → JSON
#         ))
#         con.commit()
#     finally:
#         cur.close()
#         con.close()

#     return jsonify({"status": "ok"})


# @app.route("/api/clients")
# def api_clients():
#     """Return all clients (with optional search)."""
#     search = request.args.get("search", "").lower()

#     con = get_db()
#     cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
#     cur.execute("SELECT * FROM clients")
#     rows = cur.fetchall()
#     cur.close()
#     con.close()

#     results = []
#     for r in rows:
#         status = "online" if (datetime.datetime.utcnow() - r["last_seen"]).total_seconds() < 90 else "offline"
#         if search and search not in (r["hostname"] or "").lower():
#             continue
#         results.append({
#             "uuid": r["client_uuid"],
#             "mac": r["mac"],
#             "hostname": r["hostname"],
#             "last_seen": r["last_seen"].isoformat(),
#             "ip": r["ip"],
#             "status": status
#         })

#     return jsonify(results)


# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     """Return full details for a single client."""
#     con = get_db()
#     cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
#     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     cur.close()
#     con.close()

#     if not r:
#         return jsonify({"error": "Not found"}), 404

#     return jsonify({
#         "uuid": r["client_uuid"],
#         "mac": r["mac"],
#         "hostname": r["hostname"],
#         "last_seen": r["last_seen"].isoformat(),
#         "ip": r["ip"],
#         "hardware": r["hardware"],
#         "apps": r["apps"]
#     })


# @app.route("/api/export/csv")
# def export_csv():
#     """Export all clients as CSV."""
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT client_uuid,hostname,mac,ip,last_seen FROM clients")
#     rows = cur.fetchall()
#     cur.close()
#     con.close()

#     output = io.StringIO()
#     output.write("UUID,Hostname,MAC,IP,Last Seen\n")
#     for r in rows:
#         output.write(",".join(map(str, r)) + "\n")

#     mem = io.BytesIO()
#     mem.write(output.getvalue().encode("utf-8"))
#     mem.seek(0)

#     return send_file(mem, mimetype="text/csv", download_name="clients.csv", as_attachment=True)


# @app.route("/api/export/pdf")
# def export_pdf():
#     """Export all clients as PDF."""
#     from reportlab.lib.pagesizes import letter
#     from reportlab.pdfgen import canvas

#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT hostname,ip,last_seen FROM clients")
#     rows = cur.fetchall()
#     cur.close()
#     con.close()

#     buffer = io.BytesIO()
#     c = canvas.Canvas(buffer, pagesize=letter)
#     y = 750

#     for r in rows:
#         line = f"{r[0]} | {r[1]} | {r[2]}"
#         if y < 50:
#             c.showPage()
#             y = 750
#         c.drawString(40, y, line)
#         y -= 20

#     c.save()
#     buffer.seek(0)
#     return send_file(buffer, mimetype="application/pdf", download_name="clients.pdf", as_attachment=True)


# if __name__ == "__main__":
#     init_db()
#     app.run(host="0.0.0.0", port=5000, debug=True)


















# from flask import Flask, request, jsonify, send_file
# import psycopg2, psycopg2.extras
# import json, datetime, io, os

# # ==============================
# # DATABASE CONFIG
# # ==============================

# DATABASE_URL = os.environ.get("DATABASE_URL")
# if not DATABASE_URL:
#     raise ValueError("DATABASE_URL environment variable is not set!")

# app = Flask(__name__, template_folder="templates")


# def get_db():
#     """Create new database connection."""
#     return psycopg2.connect(DATABASE_URL, sslmode="require")


# def init_db():
#     """Initialize clients table."""
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS clients (
#             client_uuid TEXT PRIMARY KEY,
#             mac TEXT,
#             hostname TEXT,
#             last_seen TIMESTAMP,
#             ip TEXT,
#             hardware JSONB,
#             apps JSONB
#         )
#     """)
#     con.commit()
#     cur.close()
#     con.close()


# # Initialize DB on startup (important for Render + Gunicorn)
# init_db()


# # ==============================
# # HOME ROUTE (FIX FOR 404)
# # ==============================

# @app.route("/")
# def home():
#     return "Server Running Successfully"


# # ==============================
# # CLIENT REPORT API
# # ==============================

# @app.route("/api/report", methods=["POST"])
# def api_report():
#     data = request.get_json()
#     ip = request.remote_addr

#     if not data:
#         return jsonify({"error": "No JSON received"}), 400

#     required = ["uuid", "mac", "hostname", "timestamp", "hardware", "apps"]
#     for r in required:
#         if r not in data:
#             return jsonify({"error": f"Missing {r}"}), 400

#     # Convert timestamp safely
#     try:
#         timestamp = datetime.datetime.fromisoformat(data["timestamp"])
#     except Exception:
#         timestamp = datetime.datetime.utcnow()

#     con = get_db()
#     cur = con.cursor()

#     try:
#         cur.execute("""
#             INSERT INTO clients (client_uuid, mac, hostname, last_seen, ip, hardware, apps)
#             VALUES (%s,%s,%s,%s,%s,%s,%s)
#             ON CONFLICT (client_uuid) DO UPDATE SET
#                 mac=EXCLUDED.mac,
#                 hostname=EXCLUDED.hostname,
#                 last_seen=EXCLUDED.last_seen,
#                 ip=EXCLUDED.ip,
#                 hardware=EXCLUDED.hardware,
#                 apps=EXCLUDED.apps
#         """, (
#             data["uuid"],
#             data["mac"],
#             data["hostname"],
#             timestamp,
#             ip,
#             json.dumps(data["hardware"]),
#             json.dumps(data["apps"])
#         ))
#         con.commit()
#     finally:
#         cur.close()
#         con.close()

#     return jsonify({"status": "ok"})


# # ==============================
# # GET ALL CLIENTS
# # ==============================

# @app.route("/api/clients")
# def api_clients():
#     search = request.args.get("search", "").lower()

#     con = get_db()
#     cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
#     cur.execute("SELECT * FROM clients ORDER BY last_seen DESC")
#     rows = cur.fetchall()
#     cur.close()
#     con.close()

#     results = []
#     now = datetime.datetime.utcnow()

#     for r in rows:
#         last_seen = r["last_seen"]

#         # Handle None safely
#         if last_seen:
#             diff = (now - last_seen).total_seconds()
#             status = "online" if diff < 90 else "offline"
#             last_seen_iso = last_seen.isoformat()
#         else:
#             status = "offline"
#             last_seen_iso = None

#         if search and search not in (r["hostname"] or "").lower():
#             continue

#         results.append({
#             "uuid": r["client_uuid"],
#             "mac": r["mac"],
#             "hostname": r["hostname"],
#             "last_seen": last_seen_iso,
#             "ip": r["ip"],
#             "status": status
#         })

#     return jsonify(results)


# # ==============================
# # GET SINGLE CLIENT
# # ==============================

# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = get_db()
#     cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
#     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     cur.close()
#     con.close()

#     if not r:
#         return jsonify({"error": "Not found"}), 404

#     return jsonify({
#         "uuid": r["client_uuid"],
#         "mac": r["mac"],
#         "hostname": r["hostname"],
#         "last_seen": r["last_seen"].isoformat() if r["last_seen"] else None,
#         "ip": r["ip"],
#         "hardware": r["hardware"],
#         "apps": r["apps"]
#     })


# # ==============================
# # EXPORT CSV
# # ==============================

# @app.route("/api/export/csv")
# def export_csv():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT client_uuid, hostname, mac, ip, last_seen FROM clients")
#     rows = cur.fetchall()
#     cur.close()
#     con.close()

#     output = io.StringIO()
#     output.write("UUID,Hostname,MAC,IP,Last Seen\n")

#     for r in rows:
#         output.write(",".join([str(x) if x else "" for x in r]) + "\n")

#     mem = io.BytesIO()
#     mem.write(output.getvalue().encode("utf-8"))
#     mem.seek(0)

#     return send_file(mem,
#                      mimetype="text/csv",
#                      download_name="clients.csv",
#                      as_attachment=True)


# # ==============================
# # EXPORT PDF
# # ==============================

# @app.route("/api/export/pdf")
# def export_pdf():
#     from reportlab.lib.pagesizes import letter
#     from reportlab.pdfgen import canvas

#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT hostname, ip, last_seen FROM clients")
#     rows = cur.fetchall()
#     cur.close()
#     con.close()

#     buffer = io.BytesIO()
#     c = canvas.Canvas(buffer, pagesize=letter)

#     y = 750
#     for r in rows:
#         line = f"{r[0]} | {r[1]} | {r[2]}"
#         if y < 50:
#             c.showPage()
#             y = 750
#         c.drawString(40, y, line)
#         y -= 20

#     c.save()
#     buffer.seek(0)

#     return send_file(buffer,
#                      mimetype="application/pdf",
#                      download_name="clients.pdf",
#                      as_attachment=True)


# # ==============================
# # RUN SERVER (RENDER SAFE)
# # ==============================

# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 10000))
#     app.run(host="0.0.0.0", port=port)









# from flask import Flask, request, jsonify, render_template, send_file
# import psycopg2, psycopg2.extras
# import json, datetime, io, os, csv
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib.pagesizes import A4

# DATABASE_URL = os.environ.get("DATABASE_URL")

# app = Flask(__name__, template_folder="templates")


# def get_db():
#     return psycopg2.connect(DATABASE_URL, sslmode="require")


# # =====================
# # HOME (Dashboard)
# # =====================
# @app.route("/")
# def home():
#     return render_template("dashboard.html")


# # =====================
# # RECEIVE CLIENT DATA
# # =====================
# @app.route("/api/report", methods=["POST"])
# def api_report():
#     data = request.get_json()
#     ip = request.remote_addr

#     con = get_db()
#     cur = con.cursor()

#     cur.execute("""
#         INSERT INTO clients (client_uuid, mac, hostname, last_seen, ip, hardware, apps)
#         VALUES (%s,%s,%s,%s,%s,%s,%s)
#         ON CONFLICT (client_uuid) DO UPDATE SET
#             mac=EXCLUDED.mac,
#             hostname=EXCLUDED.hostname,
#             last_seen=EXCLUDED.last_seen,
#             ip=EXCLUDED.ip,
#             hardware=EXCLUDED.hardware,
#             apps=EXCLUDED.apps
#     """, (
#         data["uuid"],
#         data["mac"],
#         data["hostname"],
#         datetime.datetime.fromisoformat(data["timestamp"]),
#         ip,
#         json.dumps(data["hardware"]),
#         json.dumps(data["apps"])
#     ))

#     con.commit()
#     cur.close()
#     con.close()

#     return jsonify({"status": "ok"})


# # =====================
# # GET ALL CLIENTS
# # =====================
# @app.route("/api/clients")
# def api_clients():
#     search = request.args.get("search", "").lower()

#     con = get_db()
#     cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
#     cur.execute("SELECT * FROM clients ORDER BY last_seen DESC")
#     rows = cur.fetchall()
#     cur.close()
#     con.close()

#     results = []
#     now = datetime.datetime.utcnow()

#     for r in rows:
#         diff = (now - r["last_seen"]).total_seconds()
#         status = "online" if diff < 90 else "offline"

#         if search and search not in (r["hostname"] or "").lower():
#             continue

#         results.append({
#             "uuid": r["client_uuid"],
#             "mac": r["mac"],
#             "hostname": r["hostname"],
#             "ip": r["ip"],
#             "last_seen": r["last_seen"].isoformat(),
#             "status": status
#         })

#     return jsonify(results)


# # =====================
# # GET SINGLE CLIENT
# # =====================
# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = get_db()
#     cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
#     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     cur.close()
#     con.close()

#     if not r:
#         return jsonify({"error": "Not found"}), 404

#     return jsonify({
#         "uuid": r["client_uuid"],
#         "mac": r["mac"],
#         "hostname": r["hostname"],
#         "ip": r["ip"],
#         "last_seen": r["last_seen"].isoformat(),
#         "hardware": r["hardware"],
#         "apps": r["apps"]
#     })


# # =====================
# # EXPORT CSV
# # =====================
# @app.route("/export/csv")
# def export_csv():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT client_uuid, mac, hostname, ip, last_seen FROM clients")
#     rows = cur.fetchall()
#     cur.close()
#     con.close()

#     output = io.StringIO()
#     writer = csv.writer(output)
#     writer.writerow(["UUID", "MAC", "Hostname", "IP", "Last Seen"])
#     writer.writerows(rows)

#     output.seek(0)
#     return send_file(
#         io.BytesIO(output.getvalue().encode()),
#         mimetype="text/csv",
#         as_attachment=True,
#         download_name="clients.csv"
#     )


# # =====================
# # EXPORT PDF
# # =====================
# @app.route("/export/pdf/<uuid>")
# def export_pdf(uuid):
#     con = get_db()
#     cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
#     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     cur.close()
#     con.close()

#     if not r:
#         return "Client not found", 404

#     buffer = io.BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=A4)
#     elements = []
#     styles = getSampleStyleSheet()

#     elements.append(Paragraph(f"Client: {r['hostname']}", styles["Heading1"]))
#     elements.append(Spacer(1, 12))

#     elements.append(Paragraph(f"UUID: {r['client_uuid']}", styles["Normal"]))
#     elements.append(Paragraph(f"MAC: {r['mac']}", styles["Normal"]))
#     elements.append(Paragraph(f"IP: {r['ip']}", styles["Normal"]))
#     elements.append(Paragraph(f"Last Seen: {r['last_seen']}", styles["Normal"]))

#     doc.build(elements)
#     buffer.seek(0)

#     return send_file(buffer, as_attachment=True,
#                      download_name=f"{uuid}.pdf",
#                      mimetype="application/pdf")


# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 10000))
#     app.run(host="0.0.0.0", port=port)










# import os
# import json
# import io
# import csv
# import datetime
# import psycopg2
# import psycopg2.extras

# from flask import Flask, request, jsonify, render_template, send_file, Response
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import A4

# DATABASE_URL = os.environ.get("DATABASE_URL")

# app = Flask(__name__, template_folder="templates")


# # =====================================================
# # DATABASE CONNECTION
# # =====================================================
# def get_db():
#     return psycopg2.connect(DATABASE_URL, sslmode="require")


# # =====================================================
# # SAFE JSON PARSER
# # =====================================================
# def parse_json_safe(value):
#     if isinstance(value, str):
#         try:
#             value = json.loads(value)
#             if isinstance(value, str):
#                 value = json.loads(value)
#         except:
#             return {}
#     return value


# # =====================================================
# # HOME
# # =====================================================
# @app.route("/")
# def home():
#     return render_template("dashboard.html")


# # =====================================================
# # RECEIVE CLIENT DATA
# # =====================================================
# @app.route("/api/report", methods=["POST"])
# def api_report():
#     data = request.get_json()

#     hardware = data.get("hardware", {})
#     client_ip = hardware.get("IP Address", "Unknown")

#     con = get_db()
#     cur = con.cursor()

#     cur.execute("""
#         INSERT INTO clients (client_uuid, mac, hostname, last_seen, ip, hardware, apps)
#         VALUES (%s,%s,%s,%s,%s,%s,%s)
#         ON CONFLICT (client_uuid) DO UPDATE SET
#             mac=EXCLUDED.mac,
#             hostname=EXCLUDED.hostname,
#             last_seen=EXCLUDED.last_seen,
#             ip=EXCLUDED.ip,
#             hardware=EXCLUDED.hardware,
#             apps=EXCLUDED.apps
#     """, (
#         data["uuid"],
#         data["mac"],
#         data["hostname"],
#         datetime.datetime.fromisoformat(data["timestamp"]),
#         client_ip,  # ✅ Correct IP from client
#         json.dumps(hardware),
#         json.dumps(data["apps"])
#     ))

#     con.commit()
#     cur.close()
#     con.close()

#     return jsonify({"status": "success"})


# # =====================================================
# # GET CLIENTS
# # =====================================================
# @app.route("/api/clients")
# def api_clients():
#     con = get_db()
#     cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
#     cur.execute("SELECT * FROM clients ORDER BY last_seen DESC")
#     rows = cur.fetchall()
#     cur.close()
#     con.close()

#     now = datetime.datetime.utcnow()
#     result = []

#     for r in rows:
#         diff = (now - r["last_seen"]).total_seconds()
#         status = "online" if diff < 90 else "offline"

#         result.append({
#             "uuid": r["client_uuid"],
#             "mac": r["mac"],
#             "hostname": r["hostname"],
#             "ip": r["ip"],  # ✅ Shows real client IP
#             "last_seen": r["last_seen"].isoformat(),
#             "status": status
#         })

#     return jsonify(result)


# # =====================================================
# # GET SINGLE CLIENT
# # =====================================================
# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = get_db()
#     cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
#     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     cur.close()
#     con.close()

#     if not r:
#         return jsonify({"error": "Client not found"}), 404

#     return jsonify({
#         "uuid": r["client_uuid"],
#         "mac": r["mac"],
#         "hostname": r["hostname"],
#         "ip": r["ip"],
#         "last_seen": r["last_seen"].isoformat(),
#         "hardware": parse_json_safe(r["hardware"]),
#         "apps": parse_json_safe(r["apps"])
#     })


# # =====================================================
# # EXPORT PDF (FORMATTED EXACTLY LIKE YOUR SAMPLE)
# # =====================================================
# @app.route("/export/pdf/<uuid>")
# def export_single_pdf(uuid):

#     con = get_db()
#     cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
#     cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     cur.close()
#     con.close()

#     if not r:
#         return "Client not found", 404

#     hardware = parse_json_safe(r["hardware"])
#     apps = parse_json_safe(r["apps"])

#     buffer = io.BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=A4)
#     elements = []
#     styles = getSampleStyleSheet()

#     # Title
#     elements.append(Paragraph("<b>Client Report</b>", styles["Title"]))
#     elements.append(Spacer(1, 20))

#     # -------------------------
#     # HARDWARE TABLE (Field | Value)
#     # -------------------------
#     hardware_data = [["Field", "Value"]]

#     for key, value in hardware.items():
#         hardware_data.append([str(key), str(value)])

#     hardware_table = Table(hardware_data, colWidths=[200, 300])
#     hardware_table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
#         ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
#         ('FONTSIZE', (0, 0), (-1, -1), 9),
#     ]))

#     elements.append(hardware_table)
#     elements.append(Spacer(1, 25))

#     # -------------------------
#     # APPLICATION TABLE
#     # -------------------------
#     app_data = [["Name", "Version", "Size", "Install Date"]]

#     for app in apps:
#         app_data.append([
#             app.get("name", "N/A"),
#             app.get("version", "N/A"),
#             app.get("size", "N/A"),
#             app.get("install_date", "N/A")
#         ])

#     app_table = Table(app_data, colWidths=[200, 100, 80, 120])
#     app_table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
#         ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
#         ('FONTSIZE', (0, 0), (-1, -1), 8),
#     ]))

#     elements.append(app_table)

#     doc.build(elements)
#     buffer.seek(0)

#     return send_file(
#         buffer,
#         as_attachment=True,
#         download_name=f"{uuid}_report.pdf",
#         mimetype="application/pdf"
#     )


# # =====================================================
# # RUN SERVER
# # =====================================================
# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 10000))
#     app.run(host="0.0.0.0", port=port)




















# import os
# import json
# import datetime
# import psycopg2
# from flask import Flask, jsonify, render_template, send_file, request, Response
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors
# import tempfile

# DATABASE_URL = os.environ.get("DATABASE_URL")

# app = Flask(__name__, template_folder="templates")

# # ---------------- DATABASE ----------------
# def get_db():
#     if not DATABASE_URL:
#         raise Exception("DATABASE_URL not set")
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

# # ---------------- SAFE DB INIT (Production Safe) ----------------
# try:
#     if DATABASE_URL:
#         init_db()
#     else:
#         print("WARNING: DATABASE_URL not set")
# except Exception as e:
#     print("Database init failed:", e)

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
#     try:
#         hardware = json.loads(data["hardware"]) if isinstance(data.get("hardware"), str) else data.get("hardware", {})
#         apps = json.loads(data["apps"]) if isinstance(data.get("apps"), str) else data.get("apps", [])

#         client_ip = hardware.get("IP Address", "Unknown")

#         con = get_db()
#         cur = con.cursor()
#         cur.execute("""
#         INSERT INTO clients VALUES (%s,%s,%s,%s,%s,%s,%s)
#         ON CONFLICT(client_uuid) DO UPDATE SET
#             mac_address=EXCLUDED.mac_address,
#             hostname=EXCLUDED.hostname,
#             last_seen=EXCLUDED.last_seen,
#             client_ip=EXCLUDED.client_ip,
#             hardware_info=EXCLUDED.hardware_info,
#             installed_apps=EXCLUDED.installed_apps
#         """, (
#             data["uuid"], data["mac"], data["hostname"],
#             data["timestamp"], client_ip,
#             data["hardware"], data["apps"]
#         ))
#         con.commit()
#         con.close()

#         return jsonify({"status": "ok"})

#     except Exception as e:
#         print("Error in api_report:", e)
#         return jsonify({"error": str(e)}), 500

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
#     hw_table.setStyle(TableStyle([
#         ('GRID',(0,0),(-1,-1),0.5,colors.black),
#         ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)
#     ]))

#     elements.append(Paragraph("Hardware Info", styles["Heading2"]))
#     elements.append(hw_table)
#     elements.append(Spacer(1,12))

#     # Installed Apps Table
#     apps = safe_json(r[6])
#     apps_data = [["Installed Apps"]] + [[json.dumps(a)] for a in apps]
#     apps_table = Table(apps_data, colWidths=[470])
#     apps_table.setStyle(TableStyle([
#         ('GRID',(0,0),(-1,-1),0.5,colors.black),
#         ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)
#     ]))

#     elements.append(Paragraph("Installed Apps", styles["Heading2"]))
#     elements.append(apps_table)

#     doc.build(elements)

#     return send_file(
#         path,
#         as_attachment=True,
#         mimetype="application/pdf",
#         download_name=f"{uuid}.pdf"
#     )

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

#     return Response(
#         generate(),
#         mimetype="text/csv",
#         headers={"Content-Disposition": "attachment;filename=clients.csv"}
#     )










# import os
# import json
# import datetime
# import psycopg2
# from flask import Flask, jsonify, render_template, send_file, request, Response
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors
# import tempfile

# DATABASE_URL = os.environ.get("DATABASE_URL")
# app = Flask(__name__, template_folder="templates")

# # ---------------- DATABASE ----------------
# def get_db():
#     if not DATABASE_URL:
#         raise Exception("DATABASE_URL not set")
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

# try:
#     if DATABASE_URL:
#         init_db()
#     else:
#         print("WARNING: DATABASE_URL not set")
# except Exception as e:
#     print("Database init failed:", e)

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

# # ---------------- API ENDPOINTS ----------------

# # Receive client reports
# @app.route("/api/report", methods=["POST"])
# def api_report():
#     data = request.json
#     try:
#         hardware = json.loads(data["hardware"]) if isinstance(data.get("hardware"), str) else data.get("hardware", {})
#         apps = json.loads(data["apps"]) if isinstance(data.get("apps"), str) else data.get("apps", [])

#         client_ip = hardware.get("IP Address", "Unknown")

#         con = get_db()
#         cur = con.cursor()

#         # Update if exists
#         cur.execute("""
#             UPDATE clients SET
#                 mac_address=%s,
#                 hostname=%s,
#                 last_seen=%s,
#                 client_ip=%s,
#                 hardware_info=%s,
#                 installed_apps=%s
#             WHERE client_uuid=%s
#         """, (
#             data["mac"],
#             data["hostname"],
#             data["timestamp"],
#             client_ip,
#             data["hardware"],
#             data["apps"],
#             data["uuid"]
#         ))

#         # Insert if new
#         if cur.rowcount == 0:
#             cur.execute("""
#                 INSERT INTO clients (
#                     client_uuid, mac_address, hostname, last_seen,
#                     client_ip, hardware_info, installed_apps
#                 ) VALUES (%s,%s,%s,%s,%s,%s,%s)
#             """, (
#                 data["uuid"], data["mac"], data["hostname"],
#                 data["timestamp"], client_ip, data["hardware"], data["apps"]
#             ))

#         con.commit()
#         con.close()
#         return jsonify({"status": "ok"})
#     except Exception as e:
#         print("Error in api_report:", e)
#         return jsonify({"error": str(e)}), 500

# # List all clients with optional search
# @app.route("/api/clients")
# def api_clients():
#     search = request.args.get("search")
#     con = get_db()
#     cur = con.cursor()

#     if search:
#         cur.execute("""
#             SELECT * FROM clients
#             WHERE client_uuid ILIKE %s OR hostname ILIKE %s OR mac_address ILIKE %s OR client_ip ILIKE %s
#         """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"))
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

# # Get client details
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

# # ---------------- PDF EXPORT ----------------
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

#     hw = safe_json(r[5])
#     hw_data = [["Field", "Value"]] + [[k, str(v)] for k,v in hw.items()]
#     hw_table = Table(hw_data, colWidths=[120, 350])
#     hw_table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))

#     elements.append(Paragraph("Hardware Info", styles["Heading2"]))
#     elements.append(hw_table)
#     elements.append(Spacer(1,12))

#     apps = safe_json(r[6])
#     apps_data = [["Installed Apps"]] + [[json.dumps(a)] for a in apps]
#     apps_table = Table(apps_data, colWidths=[470])
#     apps_table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))

#     elements.append(Paragraph("Installed Apps", styles["Heading2"]))
#     elements.append(apps_table)

#     doc.build(elements)

#     return send_file(path, as_attachment=True, mimetype="application/pdf", download_name=f"{uuid}.pdf")

# # ---------------- DELETE CLIENT ----------------
# @app.route("/delete-client/<uuid>", methods=["DELETE"])
# def delete_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("DELETE FROM clients WHERE client_uuid=%s", (uuid,))
#     con.commit()
#     con.close()
#     return jsonify({"status":"deleted"})

# # ---------------- CSV EXPORT ----------------
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
#                     headers={"Content-Disposition":"attachment;filename=clients.csv"})

# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5000)











import os
import json
import datetime
import psycopg2
from flask import Flask, jsonify, render_template, send_file, request, Response
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import tempfile

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL not set")

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

try:
    init_db()
except Exception as e:
    print("Database init failed:", e)

# ---------------- HELPERS ----------------
def safe_json(v):
    try:
        return json.loads(v)
    except:
        return v

def status_from_last_seen(ts):
    try:
        t = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        delta = (datetime.datetime.now() - t).total_seconds()
        return "Online" if delta <= 60 else "Offline"
    except:
        return "Offline"

# ---------------- ROUTES ----------------
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/report", methods=["POST"])
def api_report():
    data = request.json
    try:
        hardware = safe_json(data.get("hardware", {}))
        apps = safe_json(data.get("apps", []))

        client_ip = hardware.get("IP Address") or request.remote_addr or "Unknown"

        con = get_db()
        cur = con.cursor()

        # Try UPDATE first
        cur.execute("""
            UPDATE clients SET
                mac_address=%s,
                hostname=%s,
                last_seen=%s,
                client_ip=%s,
                hardware_info=%s,
                installed_apps=%s
            WHERE client_uuid=%s
        """, (
            data["mac"],
            data["hostname"],
            data["timestamp"],
            client_ip,
            data["hardware"],
            data["apps"],
            data["uuid"]
        ))

        # If no existing row, INSERT
        if cur.rowcount == 0:
            cur.execute("""
                INSERT INTO clients (
                    client_uuid,
                    mac_address,
                    hostname,
                    last_seen,
                    client_ip,
                    hardware_info,
                    installed_apps
                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                data["uuid"],
                data["mac"],
                data["hostname"],
                data["timestamp"],
                client_ip,
                data["hardware"],
                data["apps"]
            ))

        con.commit()
        con.close()
        return jsonify({"status": "ok"})

    except Exception as e:
        print("Error in api_report:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/clients")
def api_clients():
    search = request.args.get("search")
    con = get_db()
    cur = con.cursor()

    if search:
        cur.execute("""
            SELECT * FROM clients
            WHERE client_uuid ILIKE %s OR hostname ILIKE %s OR mac_address ILIKE %s OR client_ip ILIKE %s
        """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"))
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

# ---------------- PDF EXPORT ----------------
@app.route("/export/pdf/<uuid>")
def export_pdf(uuid):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM clients WHERE client_uuid=%s", (uuid,))
    r = cur.fetchone()
    con.close()

    if not r:
        return "Client not found", 404

    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Client Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    hw = safe_json(r[5])
    hw_data = [["Field", "Value"]] + [[k, str(v)] for k, v in hw.items()]
    hw_table = Table(hw_data, colWidths=[120, 350])
    hw_table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.5,colors.black),
        ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)
    ]))
    elements.append(Paragraph("Hardware Info", styles["Heading2"]))
    elements.append(hw_table)
    elements.append(Spacer(1,12))

    apps = safe_json(r[6])
    apps_data = [["Installed Apps"]]
    for a in apps:
        if isinstance(a, dict):
            name = a.get("name", str(a))
            apps_data.append([name])
        else:
            apps_data.append([str(a)])

    apps_table = Table(apps_data, colWidths=[470])
    apps_table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.5,colors.black),
        ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)
    ]))
    elements.append(Paragraph("Installed Apps", styles["Heading2"]))
    elements.append(apps_table)

    doc.build(elements)

    return send_file(path, as_attachment=True, mimetype="application/pdf", download_name=f"{uuid}.pdf")

# ---------------- CSV EXPORT ----------------
@app.route("/export/csv")
def export_csv():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT client_uuid, mac_address, hostname, last_seen, client_ip FROM clients")
    rows = cur.fetchall()
    con.close()

    def generate():
        yield "UUID,MAC,Hostname,Last Seen,IP\n"
        for r in rows:
            yield f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]}\n"

    return Response(generate(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=clients.csv"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
