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











# import os
# import json
# import datetime
# import psycopg2
# from flask import Flask, jsonify, render_template, request, Response
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors
# import tempfile

# DATABASE_URL = os.environ.get("DATABASE_URL")  # Set in Render environment

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
#         CREATE TABLE IF NOT EXISTS clients (
#             client_uuid TEXT PRIMARY KEY,
#             mac_address TEXT,
#             hostname TEXT,
#             last_seen TIMESTAMP,
#             ip TEXT,
#             hardware JSONB,
#             apps JSONB
#         )
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
# def status_from_last_seen(ts):
#     try:
#         t = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
#         return "Online" if (datetime.datetime.utcnow() - t).total_seconds() <= 120 else "Offline"
#     except:
#         return "Offline"

# def safe_json(v):
#     try:
#         return json.loads(v)
#     except:
#         return v

# # ---------------- ROUTES ----------------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")

# @app.route("/api/report", methods=["POST"])
# def api_report():
#     data = request.json
#     try:
#         hardware = json.dumps(data.get("hardware", {}))
#         apps = json.dumps(data.get("apps", []))

#         con = get_db()
#         cur = con.cursor()

#         # UPDATE if exists
#         cur.execute("""
#             UPDATE clients SET
#                 mac_address=%s,
#                 hostname=%s,
#                 last_seen=%s,
#                 ip=%s,
#                 hardware=%s,
#                 apps=%s
#             WHERE client_uuid=%s
#         """, (
#             data.get("mac"),
#             data.get("hostname"),
#             data.get("timestamp"),
#             data.get("hardware", {}).get("IP Address"),
#             hardware,
#             apps,
#             data.get("uuid")
#         ))

#         # INSERT if not exists
#         if cur.rowcount == 0:
#             cur.execute("""
#                 INSERT INTO clients (client_uuid, mac_address, hostname, last_seen, ip, hardware, apps)
#                 VALUES (%s,%s,%s,%s,%s,%s,%s)
#             """, (
#                 data.get("uuid"),
#                 data.get("mac"),
#                 data.get("hostname"),
#                 data.get("timestamp"),
#                 data.get("hardware", {}).get("IP Address"),
#                 hardware,
#                 apps
#             ))

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
#             SELECT client_uuid, hostname, ip, mac_address, last_seen FROM clients
#             WHERE client_uuid ILIKE %s OR hostname ILIKE %s OR mac_address ILIKE %s OR ip ILIKE %s
#         """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"))
#     else:
#         cur.execute("SELECT client_uuid, hostname, ip, mac_address, last_seen FROM clients")

#     rows = cur.fetchall()
#     con.close()

#     result = []
#     for r in rows:
#         last_seen_str = r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else "Unknown"
#         result.append({
#             "uuid": r[0],
#             "hostname": r[1],
#             "ip": r[2],
#             "mac": r[3],
#             "last_seen": last_seen_str,
#             "status": status_from_last_seen(last_seen_str)
#         })
#     return jsonify(result)

# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT client_uuid, hostname, ip, mac_address, last_seen, hardware, apps FROM clients WHERE client_uuid=%s", (uuid,))
#     r = cur.fetchone()
#     con.close()

#     if not r:
#         return jsonify({"error": "Client not found"}), 404

#     last_seen_str = r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else "Unknown"

#     return jsonify({
#         "uuid": r[0],
#         "hostname": r[1],
#         "ip": r[2],
#         "mac": r[3],
#         "last_seen": last_seen_str,
#         "hardware": safe_json(r[5]),
#         "apps": safe_json(r[6])
#     })

# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5000)


















# import os
# import json
# import datetime
# import psycopg2
# from flask import Flask, jsonify, render_template, request, Response
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
#     return psycopg2.connect(DATABASE_URL, sslmode="require")

# def init_db():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS clients (
#             client_uuid TEXT PRIMARY KEY,
#             mac_address TEXT,
#             hostname TEXT,
#             last_seen TIMESTAMP,
#             ip TEXT,
#             hardware JSONB,
#             apps JSONB
#         )
#     """)
#     con.commit()
#     con.close()

# if DATABASE_URL:
#     init_db()

# # ---------------- HELPERS ----------------

# def status_from_last_seen(ts):
#     try:
#         return "Online" if (datetime.datetime.utcnow() - ts).total_seconds() <= 120 else "Offline"
#     except:
#         return "Offline"

# def safe_json(v):
#     try:
#         return v if isinstance(v, (dict, list)) else json.loads(v)
#     except:
#         return {}

# # ---------------- ROUTES ----------------

# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")

# @app.route("/client/<uuid>")
# def client_page(uuid):
#     return render_template("dashboard.html")

# # ---------------- API ----------------

# @app.route("/api/report", methods=["POST"])
# def api_report():
#     data = request.json

#     hardware = json.dumps(data.get("hardware", {}))
#     apps = json.dumps(data.get("apps", []))

#     con = get_db()
#     cur = con.cursor()

#     cur.execute("""
#         INSERT INTO clients (client_uuid, mac_address, hostname, last_seen, ip, hardware, apps)
#         VALUES (%s,%s,%s,%s,%s,%s,%s)
#         ON CONFLICT (client_uuid) DO UPDATE SET
#             mac_address=EXCLUDED.mac_address,
#             hostname=EXCLUDED.hostname,
#             last_seen=EXCLUDED.last_seen,
#             ip=EXCLUDED.ip,
#             hardware=EXCLUDED.hardware,
#             apps=EXCLUDED.apps
#     """, (
#         data.get("uuid"),
#         data.get("mac"),
#         data.get("hostname"),
#         data.get("timestamp"),
#         data.get("hardware", {}).get("IP Address"),
#         hardware,
#         apps
#     ))

#     con.commit()
#     con.close()

#     return jsonify({"status": "ok"})

# @app.route("/api/clients")
# def api_clients():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT client_uuid, hostname, ip, mac_address, last_seen FROM clients")
#     rows = cur.fetchall()
#     con.close()

#     result = []
#     for r in rows:
#         result.append({
#             "uuid": r[0],
#             "hostname": r[1],
#             "ip": r[2],
#             "mac": r[3],
#             "last_seen": r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else "Unknown",
#             "status": status_from_last_seen(r[4])
#         })

#     return jsonify(result)

# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         SELECT client_uuid, hostname, ip, mac_address,
#                last_seen, hardware, apps
#         FROM clients WHERE client_uuid=%s
#     """, (uuid,))
#     r = cur.fetchone()
#     con.close()

#     if not r:
#         return jsonify({"error": "Client not found"}), 404

#     return jsonify({
#         "uuid": r[0],
#         "hostname": r[1],
#         "ip": r[2],
#         "mac": r[3],
#         "last_seen": r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else "Unknown",
#         "hardware": safe_json(r[5]),
#         "apps": safe_json(r[6])
#     })

# @app.route("/api/client/<uuid>", methods=["DELETE"])
# def delete_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("DELETE FROM clients WHERE client_uuid=%s", (uuid,))
#     con.commit()
#     con.close()
#     return jsonify({"status": "deleted"})

# @app.route("/api/client/<uuid>/pdf")
# def download_pdf(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         SELECT client_uuid, hostname, ip, mac_address,
#                last_seen, hardware, apps
#         FROM clients WHERE client_uuid=%s
#     """, (uuid,))
#     r = cur.fetchone()
#     con.close()

#     if not r:
#         return "Not found", 404

#     hardware = safe_json(r[5])
#     apps = safe_json(r[6])

#     temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
#     doc = SimpleDocTemplate(temp.name, pagesize=A4)
#     elements = []
#     styles = getSampleStyleSheet()

#     elements.append(Paragraph("Client Report", styles["Title"]))
#     elements.append(Spacer(1, 12))
#     elements.append(Paragraph(f"Hostname: {r[1]}", styles["Normal"]))
#     elements.append(Paragraph(f"IP: {r[2]}", styles["Normal"]))
#     elements.append(Paragraph(f"MAC: {r[3]}", styles["Normal"]))
#     elements.append(Spacer(1, 12))

#     hw_data = [["Key", "Value"]]
#     for k, v in hardware.items():
#         hw_data.append([str(k), str(v)])

#     hw_table = Table(hw_data)
#     hw_table.setStyle(TableStyle([
#         ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
#         ('GRID',(0,0),(-1,-1),0.5,colors.grey)
#     ]))

#     elements.append(hw_table)
#     elements.append(Spacer(1, 12))

#     apps_data = [["Name","Version","Install Date","Size"]]
#     for a in apps:
#         apps_data.append([
#             a.get("name",""),
#             a.get("version",""),
#             a.get("install_date",""),
#             str(a.get("size_bytes",""))
#         ])

#     apps_table = Table(apps_data, repeatRows=1)
#     apps_table.setStyle(TableStyle([
#         ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
#         ('GRID',(0,0),(-1,-1),0.5,colors.grey)
#     ]))

#     elements.append(apps_table)
#     doc.build(elements)

#     return Response(open(temp.name,"rb"),
#                     mimetype="application/pdf",
#                     headers={"Content-Disposition":f"attachment;filename={uuid}.pdf"})

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)















# import os
# import json
# import datetime
# import psycopg2
# from flask import Flask, jsonify, render_template, request, Response
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import A4
# import tempfile

# DATABASE_URL = os.environ.get("DATABASE_URL")

# app = Flask(__name__, template_folder="templates")

# # ---------------- DATABASE ----------------

# def get_db():
#     return psycopg2.connect(DATABASE_URL, sslmode="require")

# def init_db():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS clients (
#             client_uuid TEXT PRIMARY KEY,
#             mac_address TEXT,
#             hostname TEXT,
#             last_seen TIMESTAMP,
#             ip TEXT,
#             hardware JSONB,
#             apps JSONB
#         )
#     """)
#     con.commit()
#     con.close()

# if DATABASE_URL:
#     init_db()

# # ---------------- HELPERS ----------------

# def status_from_last_seen(ts):
#     if not ts:
#         return "Offline"
#     diff = (datetime.datetime.utcnow() - ts).total_seconds()
#     return "Online" if diff <= 120 else "Offline"

# def safe_json(v):
#     try:
#         if isinstance(v, (dict, list)):
#             return v
#         return json.loads(v)
#     except:
#         return {}

# # ---------------- ROUTES ----------------

# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")

# @app.route("/client/<uuid>")
# def client_page(uuid):
#     return render_template("dashboard.html")

# # ---------------- API ----------------

# @app.route("/api/report", methods=["POST"])
# def api_report():
#     data = request.json

#     hardware = json.dumps(data.get("hardware", {}))
#     apps = json.dumps(data.get("apps", []))

#     con = get_db()
#     cur = con.cursor()

#     cur.execute("""
#         INSERT INTO clients (client_uuid, mac_address, hostname, last_seen, ip, hardware, apps)
#         VALUES (%s,%s,%s,%s,%s,%s,%s)
#         ON CONFLICT (client_uuid) DO UPDATE SET
#             mac_address=EXCLUDED.mac_address,
#             hostname=EXCLUDED.hostname,
#             last_seen=EXCLUDED.last_seen,
#             ip=EXCLUDED.ip,
#             hardware=EXCLUDED.hardware,
#             apps=EXCLUDED.apps
#     """, (
#         data.get("uuid"),
#         data.get("mac"),
#         data.get("hostname"),
#         datetime.datetime.utcnow(),  # SERVER TIME FIX
#         data.get("hardware", {}).get("IP Address"),
#         hardware,
#         apps
#     ))

#     con.commit()
#     con.close()

#     return jsonify({"status": "ok"})


# @app.route("/api/clients")
# def api_clients():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT client_uuid, hostname, ip, mac_address, last_seen FROM clients")
#     rows = cur.fetchall()
#     con.close()

#     result = []
#     for r in rows:
#         result.append({
#             "uuid": r[0],
#             "hostname": r[1],
#             "ip": r[2],
#             "mac": r[3],
#             "last_seen": r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else "Unknown",
#             "status": status_from_last_seen(r[4])
#         })

#     return jsonify(result)


# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         SELECT client_uuid, hostname, ip, mac_address,
#                last_seen, hardware, apps
#         FROM clients WHERE client_uuid=%s
#     """, (uuid,))
#     r = cur.fetchone()
#     con.close()

#     if not r:
#         return jsonify({"error": "Client not found"}), 404

#     return jsonify({
#         "uuid": r[0],
#         "hostname": r[1],
#         "ip": r[2],
#         "mac": r[3],
#         "last_seen": r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else "Unknown",
#         "hardware": safe_json(r[5]),
#         "apps": safe_json(r[6])
#     })


# @app.route("/api/client/<uuid>", methods=["DELETE"])
# def delete_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("DELETE FROM clients WHERE client_uuid=%s", (uuid,))
#     con.commit()
#     con.close()
#     return jsonify({"status": "deleted"})


# @app.route("/api/client/<uuid>/pdf")
# def download_pdf(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         SELECT hostname, ip, mac_address, hardware, apps
#         FROM clients WHERE client_uuid=%s
#     """, (uuid,))
#     r = cur.fetchone()
#     con.close()

#     if not r:
#         return "Not found", 404

#     hardware = safe_json(r[3])
#     apps = safe_json(r[4])

#     temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
#     doc = SimpleDocTemplate(temp.name, pagesize=A4)
#     elements = []
#     styles = getSampleStyleSheet()

#     elements.append(Paragraph("Client Report", styles["Title"]))
#     elements.append(Spacer(1, 12))
#     elements.append(Paragraph(f"Hostname: {r[0]}", styles["Normal"]))
#     elements.append(Paragraph(f"IP: {r[1]}", styles["Normal"]))
#     elements.append(Paragraph(f"MAC: {r[2]}", styles["Normal"]))
#     elements.append(Spacer(1, 12))

#     # Hardware Table
#     hw_data = [["Key", "Value"]]
#     for k, v in hardware.items():
#         hw_data.append([str(k), str(v)])

#     hw_table = Table(hw_data, repeatRows=1)
#     hw_table.setStyle(TableStyle([
#         ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
#         ('GRID',(0,0),(-1,-1),0.5,colors.grey)
#     ]))

#     elements.append(hw_table)
#     elements.append(Spacer(1, 12))

#     # Apps Table
#     apps_data = [["Name","Version","Install Date","Size (MB)"]]
#     for a in apps:
#         size_mb = round(a.get("size_bytes", 0) / (1024*1024), 2)
#         apps_data.append([
#             a.get("name",""),
#             a.get("version",""),
#             a.get("install_date",""),
#             str(size_mb)
#         ])

#     apps_table = Table(apps_data, repeatRows=1)
#     apps_table.setStyle(TableStyle([
#         ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
#         ('GRID',(0,0),(-1,-1),0.5,colors.grey)
#     ]))

#     elements.append(apps_table)
#     doc.build(elements)

#     return Response(open(temp.name,"rb"),
#                     mimetype="application/pdf",
#                     headers={"Content-Disposition":f"attachment;filename={uuid}.pdf"})


# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)

















# import os
# import json
# import datetime
# import psycopg2
# from flask import Flask, jsonify, render_template, request, Response
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import A4
# import tempfile

# DATABASE_URL = os.environ.get("DATABASE_URL")

# app = Flask(__name__, template_folder="templates")

# # ================= DATABASE =================

# def get_db():
#     return psycopg2.connect(DATABASE_URL, sslmode="require")

# def init_db():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS clients (
#             client_uuid TEXT PRIMARY KEY,
#             mac_address TEXT,
#             hostname TEXT,
#             last_seen TIMESTAMP,
#             ip TEXT,
#             hardware JSONB,
#             apps JSONB
#         )
#     """)
#     con.commit()
#     con.close()

# if DATABASE_URL:
#     init_db()

# # ================= HELPERS =================

# OFFLINE_SECONDS = 30  # 🔥 30 seconds timeout

# def status_from_last_seen(ts):
#     if not ts:
#         return "Offline"
#     diff = (datetime.datetime.utcnow() - ts).total_seconds()
#     return "Online" if diff <= OFFLINE_SECONDS else "Offline"

# def safe_json(v):
#     try:
#         if isinstance(v, (dict, list)):
#             return v
#         return json.loads(v)
#     except:
#         return {}

# # ================= ROUTES =================

# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")

# @app.route("/client/<uuid>")
# def client_page(uuid):
#     return render_template("dashboard.html")

# # ================= API =================

# @app.route("/api/report", methods=["POST"])
# def api_report():
#     data = request.json

#     hardware = json.dumps(data.get("hardware", {}))
#     apps = json.dumps(data.get("apps", []))

#     con = get_db()
#     cur = con.cursor()

#     cur.execute("""
#         INSERT INTO clients (client_uuid, mac_address, hostname, last_seen, ip, hardware, apps)
#         VALUES (%s,%s,%s,%s,%s,%s,%s)
#         ON CONFLICT (client_uuid) DO UPDATE SET
#             mac_address=EXCLUDED.mac_address,
#             hostname=EXCLUDED.hostname,
#             last_seen=EXCLUDED.last_seen,
#             ip=EXCLUDED.ip,
#             hardware=EXCLUDED.hardware,
#             apps=EXCLUDED.apps
#     """, (
#         data.get("uuid"),
#         data.get("mac"),
#         data.get("hostname"),
#         datetime.datetime.utcnow(),  # 🔥 SERVER TIME
#         data.get("hardware", {}).get("IP Address"),
#         hardware,
#         apps
#     ))

#     con.commit()
#     con.close()

#     return jsonify({"status": "ok"})


# @app.route("/api/clients")
# def api_clients():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT client_uuid, hostname, ip, mac_address, last_seen FROM clients ORDER BY last_seen DESC")
#     rows = cur.fetchall()
#     con.close()

#     result = []
#     for r in rows:
#         result.append({
#             "uuid": r[0],
#             "hostname": r[1],
#             "ip": r[2],
#             "mac": r[3],
#             "last_seen": r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else "Unknown",
#             "status": status_from_last_seen(r[4])
#         })

#     return jsonify(result)


# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         SELECT client_uuid, hostname, ip, mac_address,
#                last_seen, hardware, apps
#         FROM clients WHERE client_uuid=%s
#     """, (uuid,))
#     r = cur.fetchone()
#     con.close()

#     if not r:
#         return jsonify({"error": "Client not found"}), 404

#     return jsonify({
#         "uuid": r[0],
#         "hostname": r[1],
#         "ip": r[2],
#         "mac": r[3],
#         "last_seen": r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else "Unknown",
#         "status": status_from_last_seen(r[4]),
#         "hardware": safe_json(r[5]),
#         "apps": safe_json(r[6])
#     })


# @app.route("/api/client/<uuid>", methods=["DELETE"])
# def delete_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("DELETE FROM clients WHERE client_uuid=%s", (uuid,))
#     con.commit()
#     con.close()
#     return jsonify({"status": "deleted"})


# @app.route("/api/client/<uuid>/pdf")
# def download_pdf(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         SELECT hostname, ip, mac_address, hardware, apps
#         FROM clients WHERE client_uuid=%s
#     """, (uuid,))
#     r = cur.fetchone()
#     con.close()

#     if not r:
#         return "Not found", 404

#     hardware = safe_json(r[3])
#     apps = safe_json(r[4])

#     temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
#     doc = SimpleDocTemplate(temp.name, pagesize=A4)
#     elements = []
#     styles = getSampleStyleSheet()

#     elements.append(Paragraph("Client System Report", styles["Title"]))
#     elements.append(Spacer(1, 15))

#     elements.append(Paragraph(f"<b>Hostname:</b> {r[0]}", styles["Normal"]))
#     elements.append(Paragraph(f"<b>IP:</b> {r[1]}", styles["Normal"]))
#     elements.append(Paragraph(f"<b>MAC:</b> {r[2]}", styles["Normal"]))
#     elements.append(Spacer(1, 20))

#     # Hardware
#     hw_data = [["Key", "Value"]]
#     for k, v in hardware.items():
#         if k != "Disks":
#             hw_data.append([str(k), str(v)])

#     hw_table = Table(hw_data, repeatRows=1)
#     hw_table.setStyle(TableStyle([
#         ('BACKGROUND',(0,0),(-1,0),colors.grey),
#         ('TEXTCOLOR',(0,0),(-1,0),colors.white),
#         ('GRID',(0,0),(-1,-1),0.5,colors.grey),
#     ]))

#     elements.append(hw_table)
#     elements.append(Spacer(1, 20))

#     # Disks
#     disks = hardware.get("Disks", [])
#     if disks:
#         disk_data = [["Drive", "Total (GB)", "Used (GB)", "Free (GB)"]]
#         for d in disks:
#             disk_data.append([
#                 d.get("Device") or d.get("Mountpoint"),
#                 str(d.get("Total (GB)", "")),
#                 str(d.get("Used (GB)", "")),
#                 str(d.get("Free (GB)", ""))
#             ])

#         disk_table = Table(disk_data, repeatRows=1)
#         disk_table.setStyle(TableStyle([
#             ('BACKGROUND',(0,0),(-1,0),colors.grey),
#             ('TEXTCOLOR',(0,0),(-1,0),colors.white),
#             ('GRID',(0,0),(-1,-1),0.5,colors.grey),
#         ]))

#         elements.append(disk_table)
#         elements.append(Spacer(1, 20))

#     # Apps
#     apps_data = [["Name", "Version", "Install Date", "Size (MB)"]]
#     for a in apps:
#         size_mb = round(a.get("size_bytes", 0) / (1024*1024), 2)
#         apps_data.append([
#             a.get("name",""),
#             a.get("version",""),
#             a.get("install_date",""),
#             str(size_mb)
#         ])

#     apps_table = Table(apps_data, repeatRows=1)
#     apps_table.setStyle(TableStyle([
#         ('BACKGROUND',(0,0),(-1,0),colors.grey),
#         ('TEXTCOLOR',(0,0),(-1,0),colors.white),
#         ('GRID',(0,0),(-1,-1),0.5,colors.grey),
#     ]))

#     elements.append(apps_table)

#     doc.build(elements)

#     return Response(open(temp.name,"rb"),
#                     mimetype="application/pdf",
#                     headers={"Content-Disposition":f"attachment;filename={uuid}.pdf"})


# # ================= RUN =================

# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)















# import os
# import json
# import datetime
# import psycopg2
# from io import BytesIO
# from flask import Flask, jsonify, render_template, request, send_file
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import A4

# # ---------------- CONFIG ----------------
# DATABASE_URL = os.environ.get("DATABASE_URL")
# OFFLINE_SECONDS = 30  # seconds to mark client offline

# app = Flask(__name__, template_folder="templates")

# # ---------------- DATABASE ----------------
# def get_db():
#     return psycopg2.connect(DATABASE_URL, sslmode="require")

# def init_db():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS clients (
#             client_uuid TEXT PRIMARY KEY,
#             mac_address TEXT,
#             hostname TEXT,
#             last_seen TIMESTAMP,
#             ip TEXT,
#             hardware JSONB,
#             apps JSONB
#         )
#     """)
#     con.commit()
#     con.close()

# if DATABASE_URL:
#     init_db()

# # ---------------- HELPERS ----------------
# def status_from_last_seen(ts):
#     if not ts:
#         return "Offline"
#     diff = (datetime.datetime.now() - ts).total_seconds()
#     return "Online" if diff <= OFFLINE_SECONDS else "Offline"

# def safe_json(v):
#     try:
#         if isinstance(v, (dict, list)):
#             return v
#         return json.loads(v)
#     except:
#         return {}

# # ---------------- ROUTES ----------------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")

# @app.route("/client/<uuid>")
# def client_page(uuid):
#     return render_template("dashboard.html")

# # ---------------- API ----------------
# @app.route("/api/report", methods=["POST"])
# def api_report():
#     data = request.json
#     hardware = json.dumps(data.get("hardware", {}))
#     apps = json.dumps(data.get("apps", []))

#     # Use server local time instead of UTC
#     last_seen = datetime.datetime.now()

#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         INSERT INTO clients (client_uuid, mac_address, hostname, last_seen, ip, hardware, apps)
#         VALUES (%s,%s,%s,%s,%s,%s,%s)
#         ON CONFLICT (client_uuid) DO UPDATE SET
#             mac_address=EXCLUDED.mac_address,
#             hostname=EXCLUDED.hostname,
#             last_seen=EXCLUDED.last_seen,
#             ip=EXCLUDED.ip,
#             hardware=EXCLUDED.hardware,
#             apps=EXCLUDED.apps
#     """, (
#         data.get("uuid"),
#         data.get("mac"),
#         data.get("hostname"),
#         last_seen,                     # Local server time
#         data.get("hardware", {}).get("IP Address"),
#         hardware,
#         apps
#     ))
#     con.commit()
#     con.close()
#     return jsonify({"status": "ok"})

# @app.route("/api/clients")
# def api_clients():
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("SELECT client_uuid, hostname, ip, mac_address, last_seen FROM clients ORDER BY last_seen DESC")
#     rows = cur.fetchall()
#     con.close()

#     result = []
#     for r in rows:
#         last_seen_str = r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else "Unknown"
#         result.append({
#             "uuid": r[0],
#             "hostname": r[1],
#             "ip": r[2],
#             "mac": r[3],
#             "last_seen": last_seen_str,
#             "status": status_from_last_seen(r[4])
#         })
#     return jsonify(result)

# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         SELECT client_uuid, hostname, ip, mac_address,
#                last_seen, hardware, apps
#         FROM clients WHERE client_uuid=%s
#     """, (uuid,))
#     r = cur.fetchone()
#     con.close()

#     if not r:
#         return jsonify({"error": "Client not found"}), 404

#     last_seen_str = r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else "Unknown"

#     return jsonify({
#         "uuid": r[0],
#         "hostname": r[1],
#         "ip": r[2],
#         "mac": r[3],
#         "last_seen": last_seen_str,
#         "status": status_from_last_seen(r[4]),
#         "hardware": safe_json(r[5]),
#         "apps": safe_json(r[6])
#     })

# @app.route("/api/client/<uuid>", methods=["DELETE"])
# def delete_client(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("DELETE FROM clients WHERE client_uuid=%s", (uuid,))
#     con.commit()
#     con.close()
#     return jsonify({"status": "deleted"})

# # ---------------- PDF EXPORT ----------------
# @app.route("/api/client/<uuid>/pdf")
# def download_pdf(uuid):
#     con = get_db()
#     cur = con.cursor()
#     cur.execute("""
#         SELECT hostname, ip, mac_address, hardware, apps
#         FROM clients WHERE client_uuid=%s
#     """, (uuid,))
#     r = cur.fetchone()
#     con.close()

#     if not r:
#         return "Not found", 404

#     hardware = safe_json(r[3])
#     apps = safe_json(r[4])

#     buffer = BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=A4)
#     elements = []
#     styles = getSampleStyleSheet()

#     elements.append(Paragraph("Client System Report", styles["Title"]))
#     elements.append(Spacer(1, 15))
#     elements.append(Paragraph(f"<b>Hostname:</b> {r[0]}", styles["Normal"]))
#     elements.append(Paragraph(f"<b>IP:</b> {r[1]}", styles["Normal"]))
#     elements.append(Paragraph(f"<b>MAC:</b> {r[2]}", styles["Normal"]))
#     elements.append(Spacer(1, 20))

#     # Hardware Table
#     hw_data = [["Key", "Value"]]
#     for k, v in hardware.items():
#         if k != "Disks":
#             hw_data.append([str(k), str(v)])
#     hw_table = Table(hw_data, repeatRows=1)
#     hw_table.setStyle(TableStyle([
#         ('BACKGROUND',(0,0),(-1,0),colors.grey),
#         ('TEXTCOLOR',(0,0),(-1,0),colors.white),
#         ('GRID',(0,0),(-1,-1),0.5,colors.grey),
#     ]))
#     elements.append(hw_table)
#     elements.append(Spacer(1,15))

#     # Disks Table
#     disks = hardware.get("Disks", [])
#     if disks:
#         disk_data = [["Drive", "Total (GB)", "Used (GB)", "Free (GB)"]]
#         for d in disks:
#             disk_data.append([
#                 d.get("Device") or d.get("Mountpoint"),
#                 str(d.get("Total (GB)", "")),
#                 str(d.get("Used (GB)", "")),
#                 str(d.get("Free (GB)", ""))
#             ])
#         disk_table = Table(disk_data, repeatRows=1)
#         disk_table.setStyle(TableStyle([
#             ('BACKGROUND',(0,0),(-1,0),colors.grey),
#             ('TEXTCOLOR',(0,0),(-1,0),colors.white),
#             ('GRID',(0,0),(-1,-1),0.5,colors.grey),
#         ]))
#         elements.append(disk_table)
#         elements.append(Spacer(1,15))

#     # Apps Table
#     apps_data = [["Name", "Version", "Install Date", "Size (MB)"]]
#     for a in apps:
#         try:
#             size_bytes = int(a.get("size_bytes", 0))
#         except (ValueError, TypeError):
#             size_bytes = 0
#         size_mb = round(size_bytes / (1024*1024), 2)
#         apps_data.append([
#             a.get("name",""),
#             a.get("version",""),
#             a.get("install_date",""),
#             str(size_mb)
#         ])
#     apps_table = Table(apps_data, repeatRows=1)
#     apps_table.setStyle(TableStyle([
#         ('BACKGROUND',(0,0),(-1,0),colors.grey),
#         ('TEXTCOLOR',(0,0),(-1,0),colors.white),
#         ('GRID',(0,0),(-1,-1),0.5,colors.grey),
#     ]))
#     elements.append(apps_table)

#     doc.build(elements)
#     buffer.seek(0)
#     return send_file(buffer, as_attachment=True, download_name=f"{uuid}.pdf", mimetype="application/pdf")

# # ---------------- RUN ----------------
# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)













import os
import json
import datetime
import psycopg2
from flask import Flask, jsonify, render_template, request, send_file
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
import tempfile
import csv

DATABASE_URL = os.environ.get("DATABASE_URL")

app = Flask(__name__, template_folder="templates")

# ================= DATABASE =================

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require" if DATABASE_URL else None)

def init_db():
    con = get_db()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_uuid TEXT PRIMARY KEY,
            mac_address TEXT,
            hostname TEXT,
            last_seen TIMESTAMP,
            ip TEXT,
            hardware JSONB,
            apps JSONB
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_history (
            id SERIAL PRIMARY KEY,
            client_uuid TEXT,
            app_name TEXT,
            version TEXT,
            install_date TEXT,
            size_bytes BIGINT,
            timestamp TIMESTAMP
        )
    """)

    con.commit()
    con.close()

if DATABASE_URL:
    init_db()

# ================= HELPERS =================

OFFLINE_SECONDS = 30

def status_from_last_seen(ts):
    if not ts:
        return "Offline"
    diff = (datetime.datetime.now() - ts).total_seconds()
    return "Online" if diff <= OFFLINE_SECONDS else "Offline"

def safe_json(v):
    try:
        if isinstance(v, (dict, list)):
            return v
        return json.loads(v)
    except:
        return {}

def format_size(bytes_val):
    if not bytes_val:
        return "0 MB"
    mb = bytes_val / (1024*1024)
    if mb < 1024:
        return f"{mb:.2f} MB"
    return f"{mb/1024:.2f} GB"

# ================= ROUTES =================

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/client/<uuid>")
def client_view(uuid):
    return render_template("dashboard.html")

# ================= API =================

@app.route("/api/report", methods=["POST"])
def api_report():
    data = request.json
    local_ip = data.get("hardware", {}).get("IP Address", "")

    hardware = json.dumps(data.get("hardware", {}))
    apps = data.get("apps", [])

    con = get_db()
    cur = con.cursor()

    cur.execute("""
        INSERT INTO clients (client_uuid, mac_address, hostname, last_seen, ip, hardware, apps)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (client_uuid) DO UPDATE SET
            mac_address=EXCLUDED.mac_address,
            hostname=EXCLUDED.hostname,
            last_seen=EXCLUDED.last_seen,
            ip=EXCLUDED.ip,
            hardware=EXCLUDED.hardware,
            apps=EXCLUDED.apps
    """, (
        data.get("uuid"),
        data.get("mac"),
        data.get("hostname"),
        datetime.datetime.now(),
        local_ip,
        hardware,
        json.dumps(apps)
    ))

    # App history
    for a in apps:
        app_name = a.get("name")
        version = a.get("version")
        install_date = a.get("install_date")
        size_bytes = int(a.get("size_bytes", 0))

        cur.execute("""
            SELECT version, size_bytes FROM app_history
            WHERE client_uuid=%s AND app_name=%s
            ORDER BY timestamp DESC LIMIT 1
        """, (data.get("uuid"), app_name))
        last = cur.fetchone()

        if not last or last[0] != version or int(last[1]) != size_bytes:
            cur.execute("""
                INSERT INTO app_history
                (client_uuid, app_name, version, install_date, size_bytes, timestamp)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                data.get("uuid"),
                app_name,
                version,
                install_date,
                size_bytes,
                datetime.datetime.now()
            ))

    con.commit()
    con.close()
    return jsonify({"status": "ok"})

# ================= CLIENT LIST =================

@app.route("/api/clients")
def api_clients():
    search = request.args.get("search", "").lower()
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT client_uuid, hostname, ip, mac_address, last_seen
        FROM clients ORDER BY last_seen DESC
    """)
    rows = cur.fetchall()
    con.close()

    result = []
    for r in rows:
        hostname = r[1] or ""
        if search and search not in hostname.lower():
            continue
        result.append({
            "uuid": r[0],
            "hostname": hostname,
            "ip": r[2] or "",
            "mac": r[3] or "",
            "last_seen": r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else "Unknown",
            "status": status_from_last_seen(r[4])
        })
    return jsonify(result)

# ================= SINGLE CLIENT =================

@app.route("/api/client/<uuid>")
def api_client(uuid):
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT client_uuid, hostname, ip, mac_address, last_seen, hardware, apps
        FROM clients WHERE client_uuid=%s
    """, (uuid,))
    r = cur.fetchone()
    con.close()
    if not r:
        return jsonify({"error": "Client not found"}), 404

    return jsonify({
        "uuid": r[0],
        "hostname": r[1],
        "ip": r[2],
        "mac": r[3],
        "last_seen": r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else "Unknown",
        "status": status_from_last_seen(r[4]),
        "hardware": safe_json(r[5]),
        "apps": safe_json(r[6])
    })

# ================= DELETE CLIENT =================

@app.route("/api/client/<uuid>", methods=["DELETE"])
def delete_client(uuid):
    try:
        con = get_db()
        cur = con.cursor()
        cur.execute("DELETE FROM app_history WHERE client_uuid=%s", (uuid,))
        cur.execute("DELETE FROM clients WHERE client_uuid=%s", (uuid,))
        con.commit()
        con.close()
        return jsonify({"status": "deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================= APP HISTORY =================

@app.route("/api/client/<uuid>/history")
def get_app_history(uuid):
    app_name = request.args.get("app")
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT timestamp, version, install_date, size_bytes
        FROM app_history
        WHERE client_uuid=%s AND app_name=%s
        ORDER BY timestamp DESC
    """, (uuid, app_name))
    rows = cur.fetchall()
    con.close()
    history = [{"timestamp": r[0].strftime("%Y-%m-%d %H:%M:%S"),
                "version": r[1],
                "install_date": r[2],
                "size_bytes": r[3]} for r in rows]
    return jsonify(history)

# ================= GLOBAL APP SEARCH =================

@app.route("/api/search/apps")
def global_app_search():
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify([])

    con = get_db()
    cur = con.cursor()
    # Group apps by client
    cur.execute("""
        SELECT c.hostname, c.client_uuid, COUNT(*)
        FROM clients c,
             jsonb_array_elements(c.apps) AS a
        WHERE a->>'name' ILIKE %s
        GROUP BY c.hostname, c.client_uuid
        ORDER BY c.hostname
    """, (f"%{name}%",))
    rows = cur.fetchall()
    con.close()

    return jsonify([{
        "hostname": r[0],
        "uuid": r[1],
        "matches": r[2]
    } for r in rows])

@app.route("/api/search/apps/<uuid>")
def global_app_details(uuid):
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify([])

    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT a->>'name',
               a->>'version',
               a->>'install_date',
               (a->>'size_bytes')::BIGINT
        FROM clients,
             jsonb_array_elements(apps) AS a
        WHERE client_uuid=%s
        AND a->>'name' ILIKE %s
        ORDER BY a->>'name'
    """, (uuid, f"%{name}%",))
    rows = cur.fetchall()
    con.close()

    return jsonify([{
        "name": r[0],
        "version": r[1],
        "install_date": r[2],
        "size_bytes": r[3]
    } for r in rows])

# ================= EXPORT PDF =================

@app.route("/api/client/<uuid>/export/pdf")
def export_pdf(uuid):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT hostname, ip, mac_address, hardware, apps FROM clients WHERE client_uuid=%s", (uuid,))
    r = cur.fetchone()
    con.close()
    if not r:
        return "Client not found", 404

    hostname, ip, mac, hardware, apps = r[0], r[1], r[2], safe_json(r[3]), safe_json(r[4])

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp_file.name, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Client Report: {hostname}", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"IP: {ip}  |  MAC: {mac}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Hardware
    elements.append(Paragraph("Hardware Info", styles["Heading2"]))
    hw_data = []
    for k, v in hardware.items():
        if k == "Disks" and isinstance(v, list):
            for d in v:
                hw_data.append([f"{d.get('Device','')}", f"Total {d.get('Total (GB)','')} GB", f"Free {d.get('Free (GB)','')} GB"])
        else:
            hw_data.append([k, str(v)])
    if hw_data:
        t = Table(hw_data, hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.grey),
                               ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
                               ("GRID",(0,0),(-1,-1),0.5,colors.white)]))
        elements.append(t)
        elements.append(Spacer(1, 12))

    # Apps
    elements.append(Paragraph("Installed Apps", styles["Heading2"]))
    app_data = [["Name","Version","Install Date","Size"]]
    for a in apps:
        app_data.append([a.get("name",""), a.get("version",""), a.get("install_date",""), format_size(a.get("size_bytes",0))])
    t = Table(app_data, hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.grey),
                           ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
                           ("GRID",(0,0),(-1,-1),0.5,colors.white)]))
    elements.append(t)

    doc.build(elements)
    return send_file(tmp_file.name, as_attachment=True, download_name=f"{hostname}.pdf")

# ================= EXPORT CSV =================

@app.route("/api/client/<uuid>/export/csv")
def export_csv(uuid):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT hostname, ip, mac_address, hardware, apps FROM clients WHERE client_uuid=%s", (uuid,))
    r = cur.fetchone()
    con.close()
    if not r:
        return "Client not found", 404

    hostname, ip, mac, hardware, apps = r[0], r[1], r[2], safe_json(r[3]), safe_json(r[4])

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    with open(tmp_file.name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Client Report"])
        writer.writerow(["Hostname", hostname])
        writer.writerow(["IP", ip])
        writer.writerow(["MAC", mac])
        writer.writerow([])
        writer.writerow(["Hardware Info"])
        for k, v in hardware.items():
            if k == "Disks" and isinstance(v, list):
                for d in v:
                    writer.writerow([d.get("Device",""), f"Total {d.get('Total (GB)','')} GB", f"Free {d.get('Free (GB)','')} GB"])
            else:
                writer.writerow([k, str(v)])
        writer.writerow([])
        writer.writerow(["Installed Apps"])
        writer.writerow(["Name","Version","Install Date","Size"])
        for a in apps:
            writer.writerow([a.get("name",""), a.get("version",""), a.get("install_date",""), format_size(a.get("size_bytes",0))])

    return send_file(tmp_file.name, as_attachment=True, download_name=f"{hostname}.csv")

# ================= RUN =================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)




