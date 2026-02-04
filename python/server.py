
# # after implementing disk size
# import threading, socket, sqlite3, json, io, csv, datetime, os, sys
# from flask import Flask, jsonify, render_template, send_file, request
# from waitress import serve
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
# from reportlab.lib.pagesizes import A4
# from reportlab.lib.styles import getSampleStyleSheet
#
# # ---------------- FORCE DB PATH ----------------
# DB_FILE = r"C:\Users\shivs\PyCharmMiscProject\client-dashboard-app\python\server_data.db"
# TEMPLATE_DIR = os.path.join(os.path.dirname(DB_FILE), "templates")
#
# print("SERVER DB PATH:", DB_FILE)
# print("TEMPLATE PATH:", TEMPLATE_DIR)
#
# # ---------------- CONFIG ----------------
# TCP_HOST = "10.0.5.34"
# TCP_PORT = 9002
#
# RUN_MODE = "manual"
# if "--electron" in sys.argv:
#     RUN_MODE = "electron"
#
# app = Flask(__name__, template_folder=TEMPLATE_DIR)
# shutdown_flag = threading.Event()
#
# # ---------------- DATABASE ----------------
# def init_db():
#     os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS clients (
#             client_uuid TEXT PRIMARY KEY,
#             mac_address TEXT,
#             hostname TEXT,
#             last_seen TEXT,
#             client_ip TEXT,
#             hardware_info TEXT,
#             installed_apps TEXT
#         )
#     """)
#     conn.commit()
#     conn.close()
#
#
# def upsert_client(data, ip):
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute("""
#         INSERT INTO clients VALUES (?, ?, ?, ?, ?, ?, ?)
#         ON CONFLICT(client_uuid) DO UPDATE SET
#             mac_address=excluded.mac_address,
#             hostname=excluded.hostname,
#             last_seen=excluded.last_seen,
#             client_ip=excluded.client_ip,
#             hardware_info=excluded.hardware_info,
#             installed_apps=excluded.installed_apps
#     """, (data["uuid"], data["mac"], data["hostname"], data["timestamp"], ip, data["hardware"], data["apps"]))
#     conn.commit()
#     conn.close()
#
#
# def get_all_clients():
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute("SELECT * FROM clients")
#     rows = cur.fetchall()
#     conn.close()
#     return rows
#
#
# def get_client(uuid):
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=?", (uuid,))
#     row = cur.fetchone()
#     conn.close()
#     return row
#
#
# # ---------------- TCP SERVER ----------------
# def recv_line(sock):
#     data=b""
#     while not data.endswith(b"\n"):
#         part=sock.recv(1)
#         if not part: return None
#         data+=part
#     return data.decode().strip()
#
#
# def recv_exact(sock,n):
#     data=b""
#     while len(data)<n:
#         p=sock.recv(n-len(data))
#         if not p: return None
#         data+=p
#     return data
#
#
# def recv_text(sock):
#     l=recv_line(sock)
#     if not l: return None
#     payload=recv_exact(sock,int(l))
#     return payload.decode() if payload else None
#
#
# def parse_text_data(text):
#     lines=text.splitlines()
#     data={"hardware":"","apps":""}
#     mode=None
#     for line in lines:
#         if line.startswith("CLIENT_UUID:"): data["uuid"]=line.split(":",1)[1].strip()
#         elif line.startswith("MAC_ADDRESS:"): data["mac"]=line.split(":",1)[1].strip()
#         elif line.startswith("HOSTNAME:"): data["hostname"]=line.split(":",1)[1].strip()
#         elif line.startswith("TIMESTAMP:"): data["timestamp"]=line.split(":",1)[1].strip()
#         elif line.startswith("=== HARDWARE"): mode="hw"
#         elif line.startswith("=== APPLICATIONS"): mode="apps"
#         elif mode=="hw": data["hardware"]+=line+"\n"
#         elif mode=="apps": data["apps"]+=line+"\n"
#     return data
#
#
# def handle_client(sock,addr):
#     ip,_=addr
#     cmd=recv_line(sock)
#     if cmd!="get apps":
#         sock.close()
#         return
#
#     text=recv_text(sock)
#     data=parse_text_data(text)
#
#     if "uuid" in data:
#         upsert_client(data,ip)
#         print("Saved client:", data["uuid"], "from", ip)
#
#     sock.sendall(b"OK\n")
#     sock.close()
#
#
# def tcp_server():
#     s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#     s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
#     s.bind((TCP_HOST,TCP_PORT))
#     s.listen(5)
#     print(f"[+] TCP listening {TCP_HOST}:{TCP_PORT}")
#     while not shutdown_flag.is_set():
#         try:
#             s.settimeout(1)
#             c,addr=s.accept()
#             threading.Thread(target=handle_client,args=(c,addr),daemon=True).start()
#         except socket.timeout:
#             continue
#     s.close()
#
#
# # ---------------- HELPERS ----------------
# def safe_json(v):
#     try:
#         return json.loads(v)
#     except:
#         return v.splitlines()
#
#
# def status_from_last_seen(ts):
#     try:
#         t=datetime.datetime.strptime(ts,"%Y-%m-%d %H:%M:%S")
#         return "Online" if (datetime.datetime.now()-t).seconds<=60 else "Offline"
#     except:
#         return "Offline"
#
#
# # ---------------- FLASK ROUTES ----------------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")
#
#
# @app.route("/api/clients")
# def api_clients():
#     rows=get_all_clients()
#     return jsonify([{
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "last_seen":r[3],
#         "ip":r[4],
#         "status":status_from_last_seen(r[3])
#     } for r in rows])
#
#
# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     r=get_client(uuid)
#     return jsonify({
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "last_seen":r[3],
#         "ip":r[4],
#         "hardware":safe_json(r[5]),
#         "apps":safe_json(r[6])
#     })
#
#
# @app.route("/export/csv")
# def export_csv():
#     rows = get_all_clients()
#     output = io.StringIO()
#     writer = csv.writer(output)
#     writer.writerow(["UUID","MAC","Hostname","Last Seen","IP","Hardware","Apps"])
#     for r in rows:
#         writer.writerow(r)
#     output.seek(0)
#     return send_file(io.BytesIO(output.getvalue().encode()),
#                      mimetype="text/csv",
#                      as_attachment=True,
#                      download_name="clients.csv")
#
#
# @app.route("/export/pdf/<uuid>")
# def export_pdf(uuid):
#     r = get_client(uuid)
#     if not r:
#         return "Client not found", 404
#
#     buffer = io.BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=A4)
#     styles = getSampleStyleSheet()
#     elements = []
#
#     elements.append(Paragraph("Client Report", styles["Title"]))
#     elements.append(Spacer(1, 12))
#
#     labels = ["UUID","MAC","Hostname","Last Seen","IP"]
#     for l,v in zip(labels,r[:5]):
#         elements.append(Paragraph(f"<b>{l}:</b> {v}", styles["Normal"]))
#         elements.append(Spacer(1,6))
#
#     elements.append(Spacer(1,12))
#     elements.append(Paragraph("Hardware", styles["Heading2"]))
#     for line in safe_json(r[5]):
#         elements.append(Paragraph(line, styles["Normal"]))
#
#     elements.append(Spacer(1,12))
#     elements.append(Paragraph("Applications", styles["Heading2"]))
#     for a in safe_json(r[6]):
#         elements.append(Paragraph(str(a), styles["Normal"]))
#
#     doc.build(elements)
#     buffer.seek(0)
#
#     return send_file(buffer, as_attachment=True,
#                      download_name=f"{uuid}.pdf",
#                      mimetype="application/pdf")
#
#
# @app.route("/shutdown", methods=["POST"])
# def shutdown():
#     print("Shutdown requested")
#     shutdown_flag.set()
#     os._exit(0)
#
#
# # ---------------- RUN ----------------
# if __name__=="__main__":
#     init_db()
#     threading.Thread(target=tcp_server,daemon=True).start()
#     serve(app, host="10.0.5.34", port=9001)













# #  recent changes added
#
# import threading, socket, sqlite3, json, io, csv, datetime, os, sys
# from flask import Flask, jsonify, render_template, send_file, request
# from waitress import serve
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
# from reportlab.lib.pagesizes import A4
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors
#
# DB_FILE = r"C:\Users\shivs\PyCharmMiscProject\client-dashboard-app\python\server_data.db"
# TEMPLATE_DIR = os.path.join(os.path.dirname(DB_FILE), "templates")
#
# TCP_HOST = "10.0.5.28"
# TCP_PORT = 9002
#
# app = Flask(__name__, template_folder=TEMPLATE_DIR)
# shutdown_flag = threading.Event()
#
#
# # ---------------- DATABASE ----------------
# def init_db():
#     os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#
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
#
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS app_history (
#         client_uuid TEXT,
#         app_name TEXT,
#         version TEXT,
#         size TEXT,
#         timestamp TEXT
#     )""")
#
#     def add_col(table, col, typ):
#         try:
#             cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
#         except:
#             pass
#
#     add_col("clients", "mac_address", "TEXT")
#     add_col("clients", "client_ip", "TEXT")
#     add_col("clients", "hardware_info", "TEXT")
#     add_col("clients", "installed_apps", "TEXT")
#     add_col("app_history", "size", "TEXT")
#
#     con.commit()
#     con.close()
#
#
# def upsert_client(data, ip):
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#
#     cur.execute("""
#     INSERT INTO clients VALUES (?, ?, ?, ?, ?, ?, ?)
#     ON CONFLICT(client_uuid) DO UPDATE SET
#         mac_address=excluded.mac_address,
#         hostname=excluded.hostname,
#         last_seen=excluded.last_seen,
#         client_ip=excluded.client_ip,
#         hardware_info=excluded.hardware_info,
#         installed_apps=excluded.installed_apps
#     """, (data["uuid"], data["mac"], data["hostname"], data["timestamp"], ip, data["hardware"], data["apps"]))
#
#     # Save app history
#     for line in data["apps"].splitlines():
#         if "|" in line:
#             p, v, d, s = line.split("|", 3)
#             cur.execute("""
#             INSERT INTO app_history VALUES (?,?,?,?,?)
#             """, (data["uuid"], p, v, s, data["timestamp"]))
#
#     con.commit()
#     con.close()
#
#
# def get_all_clients():
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients")
#     rows = cur.fetchall()
#     con.close()
#     return rows
#
#
# def get_client(uuid):
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=?", (uuid,))
#     row = cur.fetchone()
#     con.close()
#     return row
#
#
# # ---------------- TCP SERVER ----------------
# def recv_line(sock):
#     data=b""
#     while not data.endswith(b"\n"):
#         p=sock.recv(1)
#         if not p: return None
#         data+=p
#     return data.decode().strip()
#
#
# def recv_exact(sock,n):
#     data=b""
#     while len(data)<n:
#         p=sock.recv(n-len(data))
#         if not p: return None
#         data+=p
#     return data
#
#
# def recv_text(sock):
#     l=recv_line(sock)
#     if not l: return None
#     payload=recv_exact(sock,int(l))
#     return payload.decode() if payload else None
#
#
# def parse_text_data(text):
#     lines=text.splitlines()
#     data={"hardware":"","apps":""}
#     mode=None
#     for line in lines:
#         if line.startswith("CLIENT_UUID:"): data["uuid"]=line.split(":",1)[1].strip()
#         elif line.startswith("MAC_ADDRESS:"): data["mac"]=line.split(":",1)[1].strip()
#         elif line.startswith("HOSTNAME:"): data["hostname"]=line.split(":",1)[1].strip()
#         elif line.startswith("TIMESTAMP:"): data["timestamp"]=line.split(":",1)[1].strip()
#         elif line.startswith("=== HARDWARE"): mode="hw"
#         elif line.startswith("=== APPLICATIONS"): mode="apps"
#         elif mode=="hw": data["hardware"]+=line+"\n"
#         elif mode=="apps": data["apps"]+=line+"\n"
#     return data
#
#
# def handle_client(sock,addr):
#     ip,_=addr
#     cmd=recv_line(sock)
#     if cmd!="get apps":
#         sock.close()
#         return
#     text=recv_text(sock)
#     data=parse_text_data(text)
#     if "uuid" in data:
#         upsert_client(data,ip)
#     sock.sendall(b"OK\n")
#     sock.close()
#
#
# def tcp_server():
#     s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#     s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
#     s.bind((TCP_HOST,TCP_PORT))
#     s.listen(5)
#     print(f"[+] TCP listening {TCP_HOST}:{TCP_PORT}")
#     while not shutdown_flag.is_set():
#         try:
#             s.settimeout(1)
#             c,addr=s.accept()
#             threading.Thread(target=handle_client,args=(c,addr),daemon=True).start()
#         except socket.timeout:
#             continue
#     s.close()
#
#
# # ---------------- HELPERS ----------------
# def safe_json(v):
#     try:
#         return json.loads(v)
#     except:
#         return v.splitlines()
#
#
# def status_from_last_seen(ts):
#     try:
#         t=datetime.datetime.strptime(ts,"%Y-%m-%d %H:%M:%S")
#         return "Online" if (datetime.datetime.now()-t).seconds<=60 else "Offline"
#     except:
#         return "Offline"
#
#
# # ---------------- FLASK ROUTES ----------------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")
#
#
# @app.route("/api/clients")
# def api_clients():
#     rows=get_all_clients()
#     return jsonify([{
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "last_seen":r[3],
#         "ip":r[4],
#         "status":status_from_last_seen(r[3])
#     } for r in rows])
#
#
# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     r=get_client(uuid)
#     return jsonify({
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "last_seen":r[3],
#         "ip":r[4],
#         "hardware":safe_json(r[5]),
#         "apps":safe_json(r[6])
#     })
#
#
# @app.route("/api/client/<uuid>/app/<path:app>/history")
# def app_history(uuid, app):
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#     cur.execute("""
#     SELECT version,size,timestamp
#     FROM app_history
#     WHERE client_uuid=? AND app_name=?
#     ORDER BY timestamp DESC
#     """,(uuid,app))
#     rows = cur.fetchall()
#     con.close()
#     return jsonify(rows)
#
#
# @app.route("/export/csv")
# def export_csv():
#     rows = get_all_clients()
#     output = io.StringIO()
#     writer = csv.writer(output)
#     writer.writerow(["UUID","MAC","Hostname","Last Seen","IP","Hardware","Apps"])
#     for r in rows:
#         writer.writerow(r)
#     output.seek(0)
#     return send_file(io.BytesIO(output.getvalue().encode()),
#                      mimetype="text/csv",
#                      as_attachment=True,
#                      download_name="clients.csv")
#
#
# @app.route("/shutdown", methods=["POST"])
# def shutdown():
#     shutdown_flag.set()
#     os._exit(0)
#
#
# # ---------------- RUN ----------------
# if __name__=="__main__":
#     init_db()
#     threading.Thread(target=tcp_server,daemon=True).start()
#     serve(app, host="10.0.5.28", port=9001)












# # #  recent changes added  currently running
# import threading, socket, sqlite3, json, io, csv, datetime, os, tempfile
# from flask import Flask, jsonify, render_template, send_file, request
# from waitress import serve
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors
#
# DB_FILE = r"C:\Users\shivs\PyCharmMiscProject\client-dashboard-app\python\server_data.db"
# TEMPLATE_DIR = os.path.join(os.path.dirname(DB_FILE), "templates")
#
# TCP_HOST = "10.0.5.28"
# TCP_PORT = 9002
#
# app = Flask(__name__, template_folder=TEMPLATE_DIR)
# shutdown_flag = threading.Event()
#
# # ---------------- DATABASE ----------------
# def init_db():
#     os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#
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
#
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS app_history (
#         client_uuid TEXT,
#         app_name TEXT,
#         version TEXT,
#         status TEXT,
#         time TEXT
#     )""")
#
#     con.commit()
#     con.close()
#
#
# def migrate_app_history():
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#
#     cur.execute("PRAGMA table_info(app_history)")
#     cols = [c[1] for c in cur.fetchall()]
#
#     if cols == ["client_uuid", "app_name", "version", "size", "timestamp"]:
#         cur.execute("ALTER TABLE app_history RENAME TO app_history_old")
#
#         cur.execute("""
#         CREATE TABLE app_history (
#             client_uuid TEXT,
#             app_name TEXT,
#             version TEXT,
#             status TEXT,
#             time TEXT
#         )""")
#
#         cur.execute("""
#         INSERT INTO app_history (client_uuid, app_name, version, status, time)
#         SELECT client_uuid, app_name, version, 'Detected', timestamp
#         FROM app_history_old
#         """)
#
#         cur.execute("DROP TABLE app_history_old")
#         con.commit()
#
#     con.close()
#
#
# def upsert_client(data, ip):
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#
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
#
#     for line in data["apps"].splitlines():
#         if "|" in line:
#             name, version, install_date, _ = line.split("|", 3)
#             time_val = install_date if install_date != "-" else data["timestamp"]
#             cur.execute("INSERT INTO app_history VALUES (?,?,?,?,?)",
#                         (data["uuid"], name, version, "Installed", time_val))
#
#     con.commit()
#     con.close()
#
#
# # ---------------- HELPERS ----------------
# def safe_json(v):
#     try:
#         return json.loads(v)
#     except:
#         return v.splitlines()
#
#
# def status_from_last_seen(ts):
#     try:
#         t=datetime.datetime.strptime(ts,"%Y-%m-%d %H:%M:%S")
#         return "Online" if (datetime.datetime.now()-t).seconds<=60 else "Offline"
#     except:
#         return "Offline"
#
#
# # ---------------- FLASK ROUTES ----------------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")
#
#
# @app.route("/api/clients")
# def api_clients():
#     con=sqlite3.connect(DB_FILE)
#     cur=con.cursor()
#     cur.execute("SELECT * FROM clients")
#     rows=cur.fetchall()
#     con.close()
#
#     return jsonify([{
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "last_seen":r[3],
#         "ip":r[4],
#         "status":status_from_last_seen(r[3])
#     } for r in rows])
#
#
# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con=sqlite3.connect(DB_FILE)
#     cur=con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=?", (uuid,))
#     r=cur.fetchone()
#     con.close()
#
#     return jsonify({
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "last_seen":r[3],
#         "ip":r[4],
#         "hardware":safe_json(r[5]),
#         "apps":safe_json(r[6])
#     })
#
#
# @app.route("/export/csv")
# def export_csv():
#     con=sqlite3.connect(DB_FILE)
#     cur=con.cursor()
#     cur.execute("SELECT * FROM clients")
#     rows=cur.fetchall()
#     con.close()
#
#     output = io.StringIO()
#     writer = csv.writer(output)
#     writer.writerow(["UUID","MAC","Hostname","Last Seen","IP","Hardware","Apps"])
#     for r in rows:
#         writer.writerow(r)
#     output.seek(0)
#     return send_file(io.BytesIO(output.getvalue().encode()),
#                      mimetype="text/csv",
#                      as_attachment=True,
#                      download_name="clients.csv")
#
#
# #  PDF WITH TABLES
# @app.route("/export/pdf/<uuid>")
# def export_pdf(uuid):
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=?", (uuid,))
#     r = cur.fetchone()
#     con.close()
#
#     if not r:
#         return "Client not found", 404
#
#     fd, path = tempfile.mkstemp(suffix=".pdf")
#     os.close(fd)
#
#     doc = SimpleDocTemplate(path, pagesize=A4)
#     styles = getSampleStyleSheet()
#     elements = []
#
#     elements.append(Paragraph("Client Report", styles["Title"]))
#     elements.append(Spacer(1, 12))
#
#     # Client Info Table
#     info_data = [
#         ["UUID", r[0]],
#         ["MAC", r[1]],
#         ["Hostname", r[2]],
#         ["Last Seen", r[3]],
#         ["IP", r[4]]
#     ]
#     info_table = Table(info_data, colWidths=[120, 350])
#     info_table.setStyle(TableStyle([
#         ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
#         ('GRID',(0,0),(-1,-1),0.5,colors.black)
#     ]))
#     elements.append(info_table)
#     elements.append(Spacer(1, 20))
#
#     # Hardware Table
#     elements.append(Paragraph("Hardware", styles["Heading2"]))
#     hw_data = [["Component"]]+[[line] for line in safe_json(r[5])]
#     hw_table = Table(hw_data, colWidths=[470])
#     hw_table.setStyle(TableStyle([
#         ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
#         ('GRID',(0,0),(-1,-1),0.5,colors.black)
#     ]))
#     elements.append(hw_table)
#     elements.append(Spacer(1, 20))
#
#     # Apps Table
#     elements.append(Paragraph("Applications", styles["Heading2"]))
#     app_rows = [["Name","Version","Date","Size"]]
#     for line in safe_json(r[6]):
#         if "|" in line:
#             app_rows.append(line.split("|",3))
#     app_table = Table(app_rows, colWidths=[180, 90, 100, 100])
#     app_table.setStyle(TableStyle([
#         ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
#         ('GRID',(0,0),(-1,-1),0.5,colors.black),
#         ('ALIGN',(1,1),(-1,-1),'CENTER')
#     ]))
#     elements.append(app_table)
#
#     doc.build(elements)
#
#     return send_file(path, as_attachment=True, download_name=f"{uuid}.pdf")
#
#
# @app.route("/shutdown", methods=["POST"])
# def shutdown():
#     shutdown_flag.set()
#     os._exit(0)
#
#
# # ---------------- RUN ----------------
# if __name__=="__main__":
#     init_db()
#     migrate_app_history()
#     serve(app, host="10.0.5.28", port=9001)















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
#
#
#
# DB_FILE = r"C:\Users\shivs\PyCharmMiscProject\client-dashboard-app\python\server_data.db"
# TEMPLATE_DIR = os.path.join(os.path.dirname(DB_FILE), "templates")
#
# TCP_HOST = "0.0.0.0"
# TCP_PORT = 9002
#
# app = Flask(__name__, template_folder=TEMPLATE_DIR)
# shutdown_flag = threading.Event()
#
# # ---------------- DATABASE ----------------
# def init_db():
#     os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#
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
#
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS app_history (
#         client_uuid TEXT,
#         app_name TEXT,
#         version TEXT,
#         status TEXT,
#         time TEXT
#     )""")
#
#     con.commit()
#     con.close()
#
#
# def upsert_client(data, ip):
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#
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
#
#     for line in data["apps"].splitlines():
#         if "|" in line:
#             name, version, install_date, _ = line.split("|", 3)
#             time_val = install_date if install_date != "-" else data["timestamp"]
#             cur.execute("INSERT INTO app_history VALUES (?,?,?,?,?)",
#                         (data["uuid"], name, version, "Installed", time_val))
#
#     con.commit()
#     con.close()
#
#
# # ---------------- TCP SERVER ----------------
# def recv_line(sock):
#     data = b""
#     while not data.endswith(b"\n"):
#         p = sock.recv(1)
#         if not p: return None
#         data += p
#     return data.decode().strip()
#
#
# def recv_exact(sock, n):
#     data = b""
#     while len(data) < n:
#         p = sock.recv(n - len(data))
#         if not p: return None
#         data += p
#     return data
#
#
# def recv_text(sock):
#     l = recv_line(sock)
#     if not l: return None
#     payload = recv_exact(sock, int(l))
#     return payload.decode() if payload else None
#
#
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
#
#
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
#
#
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
#
#
# # ---------------- HELPERS ----------------
# def safe_json(v):
#     try:
#         return json.loads(v)
#     except:
#         return v.splitlines()
#
#
# def status_from_last_seen(ts):
#     try:
#         t = datetime.datetime.strptime(ts,"%Y-%m-%d %H:%M:%S")
#         return "Online" if (datetime.datetime.now()-t).seconds<=60 else "Offline"
#     except:
#         return "Offline"
#
#
# # ---------------- FLASK ROUTES ----------------
# @app.route("/")
# def dashboard():
#     return render_template("dashboard.html")
#
#
# @app.route("/api/clients")
# def api_clients():
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients")
#     rows = cur.fetchall()
#     con.close()
#
#     return jsonify([{
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "last_seen":r[3],
#         "ip":r[4],
#         "status":status_from_last_seen(r[3])
#     } for r in rows])
#
#
# @app.route("/api/client/<uuid>")
# def api_client(uuid):
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=?", (uuid,))
#     r = cur.fetchone()
#     con.close()
#
#     return jsonify({
#         "uuid":r[0],
#         "mac":r[1],
#         "hostname":r[2],
#         "last_seen":r[3],
#         "ip":r[4],
#         "hardware":safe_json(r[5]),
#         "apps":safe_json(r[6])
#     })
#
#
# @app.route("/export/pdf/<uuid>")
# def export_pdf(uuid):
#     con = sqlite3.connect(DB_FILE)
#     cur = con.cursor()
#     cur.execute("SELECT * FROM clients WHERE client_uuid=?", (uuid,))
#     r = cur.fetchone()
#     con.close()
#
#     if not r:
#         return "Client not found", 404
#
#     fd, path = tempfile.mkstemp(suffix=".pdf")
#     os.close(fd)
#
#     doc = SimpleDocTemplate(path, pagesize=A4)
#     styles = getSampleStyleSheet()
#     elements = []
#
#     elements.append(Paragraph("Client Report", styles["Title"]))
#     elements.append(Spacer(1, 12))
#
#     info = [["Field","Value"],
#             ["UUID",r[0]],["MAC",r[1]],["Hostname",r[2]],
#             ["Last Seen",r[3]],["IP",r[4]]]
#
#     t1 = Table(info, colWidths=[120,350])
#     t1.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),
#                             ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
#     elements.append(t1); elements.append(Spacer(1,20))
#
#     elements.append(Paragraph("Hardware", styles["Heading2"]))
#     hw = [["Component"]] + [[l] for l in safe_json(r[5])]
#     t2 = Table(hw, colWidths=[470])
#     t2.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black)]))
#     elements.append(t2); elements.append(Spacer(1,20))
#
#     elements.append(Paragraph("Applications", styles["Heading2"]))
#     apps = [["Name","Version","Date","Size"]]
#     for l in safe_json(r[6]):
#         if "|" in l: apps.append(l.split("|",3))
#     t3 = Table(apps, colWidths=[180,90,100,100])
#     t3.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),
#                             ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
#     elements.append(t3)
#
#     doc.build(elements)
#
#     return send_file(path, as_attachment=True,
#                      mimetype="application/pdf",
#                      download_name=f"{uuid}.pdf")
#
#
# @app.route("/shutdown", methods=["POST"])
# def shutdown():
#     shutdown_flag.set()
#     os._exit(0)
#
#
# # ---------------- RUN ----------------
#
# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 9001))
#     serve(app, host="0.0.0.0", port=port)












# cloud ready server

import os, json, uuid, datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

@app.route("/")
def index():
    return "Dashboard Server Running"

@app.route("/api/clients")
def get_clients():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT uuid, hostname, last_seen, status
        FROM clients
        ORDER BY last_seen DESC
    """)
    rows = cur.fetchall()

    conn.close()
    return jsonify(rows)

@app.route("/api/client/<uuid>")
def client_detail(uuid):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT app_name, version, install_date, size, ts
        FROM reports
        WHERE uuid=%s
        ORDER BY ts DESC
    """, (uuid,))
    rows = cur.fetchall()

    conn.close()
    return jsonify(rows)

@app.route("/api/report", methods=["POST"])
def report():
    data = request.json
    uuid_ = data["uuid"]
    hostname = data["hostname"]
    hardware = data.get("hardware", {})
    apps = data.get("apps", [])

    conn = get_db()
    cur = conn.cursor()

    # Upsert client
    cur.execute("""
        INSERT INTO clients (uuid, hostname, last_seen, status, hardware)
        VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT (uuid)
        DO UPDATE SET
            hostname=EXCLUDED.hostname,
            last_seen=EXCLUDED.last_seen,
            status=EXCLUDED.status,
            hardware=EXCLUDED.hardware
    """, (uuid_, hostname, datetime.datetime.utcnow(), "Online", json.dumps(hardware)))

    # Insert reports
    for appx in apps:
        cur.execute("""
            INSERT INTO reports (uuid, app_name, version, install_date, size)
            VALUES (%s,%s,%s,%s,%s)
        """, (uuid_, appx["name"], appx["version"], appx["date"], appx["size"]))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
