import os

# List of JSONL files to check
files = [
    "usb_pd_metadata.jsonl", 
    "usb_pd_pages.jsonl", 
    "usb_pd_toc.jsonl", 
    "usb_pd_spec.jsonl"
]

print("Checking JSONL files...")
print("-" * 30)

for file in files:
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        count = len([line for line in lines if line.strip()])
        print(f"{file}: {count} records")
    else:
        print(f"{file}: NOT FOUND")

print("-" * 30)
print("Done!")
