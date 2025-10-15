#!/usr/bin/env python3
import os, sys, zipfile, hashlib, xml.etree.ElementTree as ET

REPO_ID = "repository.RepoDawg"
REPO_NAME = "RepoDawg"
PROVIDER = "Dawgfather"
RAW_BASE = "https://raw.githubusercontent.com/jason247g/RepoDawg/master"

ADDONS_DIR = "addons"
ADDONS_XML = "addons.xml"
ADDONS_MD5 = "addons.xml.md5"
REPO_FOLDER = "repository.RepoDawg"
REPO_ADDON_XML = os.path.join(REPO_FOLDER, "addon.xml")

def read_addon_meta_from_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as z:
        # find the internal addon.xml (first top-level dir /addon.xml)
        root_dir = None
        for name in z.namelist():
            parts = name.strip("/").split("/")
            if len(parts) == 2 and parts[1].lower() == "addon.xml":
                root_dir = parts[0]
                addon_xml_path = name
                break
        if not root_dir:
            raise RuntimeError(f"No addon.xml found inside {zip_path}")

        with z.open(addon_xml_path) as f:
            tree = ET.parse(f)
            root = tree.getroot()
            addon_id = root.attrib["id"]
            name = root.attrib.get("name", addon_id)
            version = root.attrib["version"]
            provider = root.attrib.get("provider-name", "")
            return {
                "id": addon_id,
                "name": name,
                "version": version,
                "provider": provider
            }

def build_addons_xml(addons_meta):
    # minimal, Kodi-compatible repository index
    lines = ["<?xml version='1.0' encoding='UTF-8'?>", "<addons>"]
    for a in sorted(addons_meta, key=lambda x: x["id"]):
        lines += [
            f"<addon id=\"{a['id']}\" name=\"{a['name']}\" version=\"{a['version']}\" provider-name=\"{a['provider'] or PROVIDER}\">",
            "    <extension point=\"xbmc.addon.metadata\">",
            f"        <summary>{a['name']}</summary>",
            f"        <description>{a['name']} add-on.</description>",
            "        <platform>all</platform>",
            "    </extension>",
            "</addon>"
        ]
    lines.append("</addons>")
    return "\n".join(lines)

def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def md5_text(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def ensure_repo_addon_xml():
    os.makedirs(REPO_FOLDER, exist_ok=True)
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<addon id="{REPO_ID}" name="{REPO_NAME}" version="1.0.6" provider-name="{PROVIDER}">
  <extension point="xbmc.addon.repository" name="{REPO_NAME}">
    <dir>
      <info compressed="false">{RAW_BASE}/{ADDONS_XML}</info>
      <checksum>{RAW_BASE}/{ADDONS_MD5}</checksum>
      <datadir zip="true">{RAW_BASE}/{ADDONS_DIR}/</datadir>
    </dir>
  </extension>
  <extension point="xbmc.addon.metadata">
    <summary>{PROVIDER}’s Kodi Repository</summary>
    <description>The official {PROVIDER} repository for Kodi add-ons.</description>
    <platform>all</platform>
    <language>en</language>
  </extension>
</addon>
"""
    write_text(REPO_ADDON_XML, content)
    print(f"wrote {REPO_ADDON_XML}")

def main():
    if not os.path.isdir(ADDONS_DIR):
        print(f"ERROR: '{ADDONS_DIR}' folder not found in repo root.")
        sys.exit(1)

    addons_meta = []
    for name in os.listdir(ADDONS_DIR):
        if not name.endswith(".zip"): 
            continue
        zip_path = os.path.join(ADDONS_DIR, name)
        meta = read_addon_meta_from_zip(zip_path)
        # validate filename pattern addon.id-version.zip
        expected = f"{meta['id']}-{meta['version']}.zip"
        if name != expected:
            print(f"WARNING: {name} should be named {expected} (rename to match).")
        addons_meta.append(meta)

    if not addons_meta:
        print("ERROR: No valid add-on zips found in ./addons/")
        sys.exit(2)

    xml = build_addons_xml(addons_meta)
    write_text(ADDONS_XML, xml)
    write_text(ADDONS_MD5, md5_text(xml))
    print(f"wrote {ADDONS_XML}")
    print(f"wrote {ADDONS_MD5}  (md5 of addons.xml)")

    ensure_repo_addon_xml()
    print("\nAll good. Commit & push these files, then reinstall the repo zip in Kodi.")

if __name__ == "__main__":
    main()
