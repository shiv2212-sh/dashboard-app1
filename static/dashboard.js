fetch("/api/clients")
  .then(r => r.json())
  .then(data => {
    let html = "<tr><th>Status</th><th>UUID</th><th>Hostname</th><th>IP</th><th>Last Seen</th><th>View</th></tr>";
    data.forEach(c => {
      html += `<tr>
        <td class="online">${c.status}</td>
        <td>${c.uuid}</td>
        <td>${c.hostname}</td>
        <td>${c.ip}</td>
        <td>${c.last_seen}</td>
        <td><a href="/client/${c.uuid}">View</a></td>
      </tr>`;
    });
    document.getElementById("clients").innerHTML = html;
  });
