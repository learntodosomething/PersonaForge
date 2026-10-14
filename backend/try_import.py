import sys, glob, httpx

folder = sys.argv[1]  # pl. C:\...\PersonaForge\data\my_chat
paths = sorted(glob.glob(f"{folder}/message_*.json"))
files = [("files", (p.split("\\")[-1], open(p, "rb"), "application/json")) for p in paths]

r = httpx.post(
    "http://127.0.0.1:8000/api/imports",
    files=files,
    data={"confirm_authorized": "true"},
    timeout=120,
)
print(r.status_code)
body = r.json()
if r.status_code == 201:
    print("import_id:", body["import_id"])
    print("riport:", body["report"])
    for s in body["speakers"]:
        print(f'{s["name"]}: {s["text_message_count"]} szöveges / {s["message_count"]} összes')
else:
    print(body)