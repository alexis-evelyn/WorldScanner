# Potentially may use official server jars with RCON
# in combination with the scanner in order to scan "not generated" chunks
import subprocess

from mcrcon import MCRcon
from typing import Optional

import os
import json
import requests

working_dir: str = "working"
jar_path: str = os.path.join(working_dir, "server.jar")
server_path: str = os.path.join(working_dir, "server")
eula_path: str = os.path.join(server_path, "eula.txt")
server_properties_path: str = os.path.join(server_path, "server.properties")
user_agent: str = "Chunk Scanner - https://github.com/alexis-evelyn/WorldScanner"
server_manifest_list: str = "https://launchermeta.mojang.com/mc/game/version_manifest.json"


def retrieve_json_document(url: str) -> Optional[dict]:
    headers: dict = {
        "User-Agent": user_agent
    }

    response: requests.Response = requests.get(url=url, headers=headers)

    if response.status_code == 200:
        results: dict = json.loads(response.text)
        return results


def retrieve_binary(url: str) -> Optional[bytes]:
    headers: dict = {
        "User-Agent": user_agent
    }

    response: requests.Response = requests.get(url=url, headers=headers)

    if response.status_code == 200:
        return response.content


def download_server_jar(manifest: str):
    server_manifest: Optional[dict] = retrieve_json_document(url=manifest)
    url: Optional[str] = None
    if server_manifest is not None:
        url: str = server_manifest["downloads"]["server"]["url"]
        jar: Optional[bytes] = retrieve_binary(url=url)
        with open(jar_path, mode="wb") as f:
            f.write(jar)
            f.close()  # Not Needed With The `with` syntax


def download_latest_release():
    # Scan For Latest Version Of Minecraft
    manifest: Optional[dict] = retrieve_json_document(url=server_manifest_list)
    url: Optional[str] = None
    if manifest is not None:
        latest_version: str = manifest["latest"]["release"]

        for version in manifest["versions"]:
            if version["id"] == latest_version:
                url: str = version["url"]

    download_server_jar(manifest=url)


# For Automatically Setting The Eula On New Jar Download
# For Obvious Reasons, The Usage Of This Script Implies Agreeing With The Eula
def set_eula(status: bool):
    # if os.path.exists(eula_path):
    #     os.remove(eula_path)

    with open(file=eula_path, mode="w") as f:
        f.write("# Automatically Written By World Scanner\n")
        f.write("# Make Sure To Agree With Mojang's EULA: https://account.mojang.com/documents/minecraft_eula\n")
        f.write("# If You Can't Comply With Mojang's EULA, Stop Using This Seed Script As We Use Mojang's Server To Generate Chunks!!!\n")
        f.write("eula=%s" % ("true" if status else "false"))  # Ternary Operation
        f.close()  # Not Needed With The `with` syntax


def setup_server_properties(world_name: str = "world", level_seed: str = "", level_type: str = "DEFAULT", generator_settings: str = "", rcon_password: Optional[str] = None, whitelist: bool = True, online: bool = False):
    # Server Property Explanation: https://minecraft.fandom.com/wiki/Server.properties
    with open(file=server_properties_path, mode="w") as f:
        # Dynamic Options
        f.write("level-name=%s\n" % world_name)
        f.write("level-seed=%s\n" % level_seed)
        f.write("level-type=%s\n" % level_type)
        f.write("generator-settings=%s\n" % generator_settings)
        f.write("rcon.password=%s\n" % ("" if rcon_password is None or rcon_password == "" else rcon_password))

        # Bot Player Settings
        # This Is For Allowing Fake Players To Be Added For Chunk Generation As Well As Opening Loot
        f.write("online-mode=%s\n" % ("true" if online else "false"))
        f.write("white-list=%s\n" % ("true" if whitelist else "false"))
        f.write("gamemode=%s\n" % "spectator")

        # section_sign_char: str = u"\u00A7"  # \u00A7 -> §  # This Screws With The Output (Not Python's Fault)
        section_sign_char: str = "\\u00A7"  # \u00A7 -> §
        motd: str = "%s6%slChunk Scanner Server" % (section_sign_char, section_sign_char)

        # MOTD Settings
        f.write("server-name=%s\n" % motd)
        f.write("motd=%s\n" % motd)  # Color Codes: https://www.digminecraft.com/lists/color_list_pc.php

        # Static Options
        f.write("server-ip=%s\n" % "127.0.0.1")
        f.write("rcon.port=%s\n" % "25575")
        f.write("server-port=%s\n" % "25565")
        f.write("allow-nether=%s\n" % ("true" if True else "false"))
        f.write("enable-rcon=%s\n" % ("true" if True else "false"))
        f.write("difficulty=%s\n" % "easy")
        f.close()  # Not Needed With The `with` syntax


# MCRCON - https://pypi.org/project/mcrcon/
# - Use /forceload, /locate, and /locatebiomes to find chunks to generate
# - Use /save-all to force server save
# - Use /whitelist and /op to OP Bot Player
# - /forceload uses BlockPos
# - /whitelist Uses The Online Mode UUID Even When Offline (Making It Useless In Offline Mode)
# For Controlling The Server Without A Fake Client
def send_rcon_message(rcon_password: str):
    with MCRcon("127.0.0.1", rcon_password) as mcr:
        resp = mcr.command("/whitelist add ScientistEvelyn")
        print(resp)


# Py4J - https://stackoverflow.com/a/3793523/6828099
def launch_server_test():
    # Variables From Manifest To Aid Launching Jar
    # server_manifest["javaVersion"]["majorVersion"]

    # Use Equivalent Of `java -jar ../server.jar nogui`
    # TODO: Implement Threading And Streaming stdin/stdout/stderr!!!
    # TODO: Check Java Version And Compare Against Manifest Minimum
    result = subprocess.run(["java", "-jar", os.path.abspath(jar_path), "nogui"], cwd=os.path.abspath(server_path), input=None, capture_output=True, timeout=None, check=False)
    print(result)


# Quarry - https://github.com/barneygale/quarry/
# - Test Script: https://github.com/barneygale/quarry/blob/master/examples/client_messenger.py
# - Use For Generating Bots To Chunk Load And Open Loot
def launch_client_test():
    pass


if __name__ == "__main__":
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)

    # I May Have The Script Delete The Server Directory And Recreate It Every Run
    if not os.path.exists(server_path):
        os.makedirs(server_path)

    if not os.path.exists(jar_path):
        download_latest_release()

    if os.path.exists(server_path):
        # TODO: Randomize Password Even Though On Localhost Only
        rcon_password: str = "kekfnejkfrenjfenjfnej"

        set_eula(status=True)
        setup_server_properties(world_name="test", level_seed="2332439756294123069", rcon_password=rcon_password)
