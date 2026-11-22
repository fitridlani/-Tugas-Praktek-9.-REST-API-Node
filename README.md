# Tugas Pengembangan — REST API Node-RED untuk IoT

## File
| File | Tujuan |
|---|---|
| `flows.json` | Import ke Node-RED (tab "IoT REST API") |
| `dashboard.html` | Taruh di `C:\node-red-static\` |
| `simulasi_esp32.py` | Simulator ESP32 (paho-mqtt v2) |

## Persiapan (sekali saja)
1. `pip install paho-mqtt`
2. Node-RED → ☰ → **Manage palette → Install** → `node-red-node-sqlite` (butuh restart Node-RED).
3. Di `settings.js` Node-RED aktifkan: `httpStatic: 'C:/node-red-static/'`, lalu restart.
4. Salin `dashboard.html` ke `C:\node-red-static\`.
5. Node-RED → ☰ → **Import** → pilih `flows.json` → **Deploy**.
   Database `iot_history.db` dibuat otomatis (relatif terhadap folder tempat Node-RED dijalankan; boleh diganti path absolut di node config SQLite).

## Menjalankan
```
Terminal 1: mosquitto -v
Terminal 2: node-red
Terminal 3: python simulasi_esp32.py
```
Buka dashboard: **http://localhost:1880/dashboard.html**

## Pemetaan 5 tugas
| # | Tugas | Implementasi |
|---|---|---|
| 1 | `PUT /api/threshold` + notifikasi | Body `{"max": 29}`. Saat suhu *baru* melewati batas: notifikasi ke MQTT `iot/notifikasi`, WebSocket, debug Node-RED, banner di dashboard. `GET /api/threshold` untuk membaca. |
| 2 | Grafik Chart.js | Suhu, kelembaban (sumbu kanan), dan garis batas suhu; 30 titik terakhir. |
| 3 | API key | Header `X-API-Key` wajib di semua endpoint (kecuali preflight OPTIONS). Salah/kosong → **401**. Key default `iot-kampus-2026` (ubah di node *Init Config* **dan** `API_KEY` di dashboard). |
| 4 | WebSocket | `ws://localhost:1880/ws/sensor`. Dashboard tanpa polling saat WS aktif; otomatis fallback polling 3 detik bila WS putus lalu reconnect. |
| 5 | SQLite | Tabel `sensor_history`; `/api/history?limit=N` (default 50, maks 500) membaca dari DB, sehingga data bertahan setelah restart. |

## Uji dengan curl
```bash
KEY="X-API-Key: iot-kampus-2026"

curl -H "$KEY" http://localhost:1880/api/suhu
curl -H "$KEY" "http://localhost:1880/api/history?limit=10"
curl -H "$KEY" http://localhost:1880/api/threshold
curl -X PUT  http://localhost:1880/api/threshold -H "$KEY" -H "Content-Type: application/json" -d '{"max":28}'
curl -X POST http://localhost:1880/api/kontrol   -H "$KEY" -H "Content-Type: application/json" -d '{"device":"lamp","action":"on"}'

# tanpa key -> 401
curl -i http://localhost:1880/api/suhu
# validasi -> 400
curl -X PUT http://localhost:1880/api/threshold -H "$KEY" -H "Content-Type: application/json" -d '{"max":"abc"}'
```
Tips: set batas 27 agar notifikasi cepat muncul (simulator menghasilkan 25–32 °C). Uji notifikasi MQTT: `mosquitto_sub -t iot/notifikasi`.

## Verifikasi end-to-end
| Komponen | Hasil yang benar |
|---|---|
| Simulator → MQTT | Terminal menampilkan `-> Publish: {...}` |
| MQTT → Node-RED | Debug panel menampilkan data sensor |
| Node-RED → REST | curl `/api/suhu` mengembalikan JSON |
| REST/WS → Web | Angka, grafik, dan tabel bergerak; mode "WebSocket" |
| Web → REST → MQTT | Klik tombol lampu → terminal simulator: `<- KONTROL diterima` |

## Perbaikan terhadap flow modul asli
- Ditambahkan node `tab` (`flow_api`) yang hilang di JSON modul (tanpa ini node tidak punya flow).
- Header CORS typo (`Access-Control-AllowOrigin`, `AccessControl-Allow-Origin`) diperbaiki; `X-API-Key` dan `PUT` ditambahkan ke preflight.
- Hanya satu node `http response` dipakai bersama oleh semua endpoint.

## Catatan
- WebSocket browser tidak bisa mengirim header kustom, jadi `/ws/sensor` tidak ikut dilindungi API key (REST tetap dilindungi). Untuk produksi, gunakan token pada query/handshake.
- Chart.js dimuat dari CDN; jika offline, unduh `chart.umd.min.js` dan ganti `src` di `dashboard.html`.
- Batas suhu dan API key disimpan di flow context (memori); kembali ke default (30 °C) saat Node-RED restart.
