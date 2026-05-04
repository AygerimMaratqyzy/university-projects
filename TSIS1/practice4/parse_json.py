import json

with open("sample-data.json") as f:
    data = json.load(f)

print("Interface Status")
print(f"{'DN':45} {'Description':15} {'Speed':8} {'MTU':6}")

for item in data["imdata"]:
    attr = item["l1PhysIf"]["attributes"]

    dn = attr["dn"]
    descr = attr["descr"]
    speed = attr["speed"]
    mtu = attr["mtu"]

    print(f"{dn:45} {descr:15} {speed:8} {mtu:6}")