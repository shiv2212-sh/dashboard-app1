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













import os, json, datetime, psycopg2
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")


# ---------------- DB ----------------
def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def safe_json(v):
    try:
        return json.loads(v) if v else []
    except:
        return []


# ---------------- INIT ----------------
def init_db():
    con = get_db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        client_uuid TEXT PRIMARY KEY,
        mac_address TEXT,
        hostname TEXT,
        last_seen TIMESTAMP,
        client_ip TEXT,
        hardware_info TEXT,
        installed_apps TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS apps_history (
        id SERIAL PRIMARY KEY,
        client_uuid TEXT,
        app_name TEXT,
        version TEXT,
        size TEXT,
        install_date TEXT,
        history TEXT
    )
    """)

    con.commit()
    cur.close()
    con.close()


# ---------------- REPORT ----------------
@app.route("/api/report", methods=["POST"])
def report():
    try:
        data = request.get_json(force=True)
        now = datetime.datetime.now()

        con = get_db()
        cur = con.cursor()

        # Upsert client
        cur.execute("""
        INSERT INTO clients VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (client_uuid) DO UPDATE SET
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
            now,
            request.remote_addr,
            data["hardware"],
            data["apps"]
        ))

        apps = safe_json(data["apps"])

        for app in apps:
            name = app.get("name")
            version = app.get("version","N/A")
            size = app.get("size","N/A")
            install_date = app.get("install_date", now.strftime("%Y-%m-%d"))
            history = app.get("history", [])

            cur.execute("""
                SELECT version, history FROM apps_history
                WHERE client_uuid=%s AND app_name=%s
            """, (data["uuid"], name))

            row = cur.fetchone()

            if row:
                old_version, old_history = row
                old_history_list = safe_json(old_history)

                if old_version != version:
                    entry = f"{now} - Version changed {old_version} → {version}"
                    old_history_list.append(entry)

                cur.execute("""
                    UPDATE apps_history
                    SET version=%s, size=%s, install_date=%s, history=%s
                    WHERE client_uuid=%s AND app_name=%s
                """, (
                    version, size, install_date, json.dumps(old_history_list),
                    data["uuid"], name
                ))

            else:
                history.append(f"{now} - Installed {version}")

                cur.execute("""
                    INSERT INTO apps_history
                    (client_uuid,app_name,version,size,install_date,history)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (
                    data["uuid"], name, version, size, install_date,
                    json.dumps(history)
                ))

        con.commit()
        cur.close()
        con.close()

        return jsonify({"status":"ok"})

    except Exception as e:
        print("ERROR /api/report:", e)
        return jsonify({"error":str(e)}),500


# ---------------- CLIENTS LIST ----------------
@app.route("/api/clients")
def get_clients():
    search = request.args.get("search","")
    con = get_db()
    cur = con.cursor()

    cur.execute("""
        SELECT client_uuid, hostname, client_ip, mac_address, last_seen
        FROM clients
        WHERE hostname ILIKE %s OR client_uuid ILIKE %s
        ORDER BY last_seen DESC
    """, (f"%{search}%", f"%{search}%"))

    rows = cur.fetchall()
    con.close()

    now = datetime.datetime.now()
    result = []

    for r in rows:
        status = "Online" if (now - r[4]).total_seconds() < 60 else "Offline"
        result.append({
            "uuid": r[0],
            "hostname": r[1],
            "ip": r[2],
            "mac": r[3],
            "last_seen": r[4].strftime("%Y-%m-%d %H:%M:%S"),
            "status": status
        })

    return jsonify(result)


# ---------------- SINGLE CLIENT ----------------
@app.route("/api/client/<uuid>")
def get_client(uuid):
    con = get_db()
    cur = con.cursor()

    cur.execute("SELECT hardware_info FROM clients WHERE client_uuid=%s", (uuid,))
    hw_row = cur.fetchone()

    cur.execute("""
        SELECT app_name,version,size,install_date,history
        FROM apps_history
        WHERE client_uuid=%s
    """, (uuid,))
    app_rows = cur.fetchall()

    con.close()

    return jsonify({
        "hardware": safe_json(hw_row[0]) if hw_row else {},
        "apps": [{
            "name": r[0],
            "version": r[1],
            "size": r[2],
            "install_date": r[3],
            "history": safe_json(r[4])
        } for r in app_rows]
    })


# ---------------- DASHBOARD ----------------
@app.route("/")
def index():
    return render_template("dashboard.html")


# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT",10000))
    print(f"🚀 Running on port {port}")
    app.run(host="0.0.0.0", port=port)
