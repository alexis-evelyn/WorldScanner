import os
import sys
import uuid
from typing import List, Optional

import nbt
from nbt.world import WorldFolder


def check_blocks(chunk: nbt.chunk, dimension: str):
    # TODO: Look Up Chunk Version Differences And Create Handlers
    #   For Each Of The Differences (Then Abstract The Data To My Own Format)
    chunk_version: Optional[int] = None

    # Cause Apparently 2b2t World Downloads Have Some Tags Missing
    if "DataVersion" in chunk:
        chunk_version: Optional[int] = chunk["DataVersion"]

    # The author themselves' mentioned just looking up the data myself and not using nbt.chunk.Chunk
    chunk_data: nbt.nbt = chunk["Level"]
    chunk_status: Optional[str] = None

    # Cause Apparently 2b2t World Downloads Have Some Tags Missing
    if "Status" in chunk_data:
        chunk_status: str = chunk_data["Status"]

    # In Chunks From Origin (0, 0, 0)
    x_pos: int = chunk_data["xPos"]
    z_pos: int = chunk_data["zPos"]

    # print(f"Dimension: %s - Chunk (%s, %s)" % (dimension, x_pos, z_pos))

    # If Not full, chunk is not fully generated yet and can be ignored for illegal item searching
    if chunk_status is not None and chunk_status.value.strip() != "full":
        return

    has_barriers: bool = False
    for section in chunk_data["Sections"]:
        if "Palette" in section:
            palette = section["Palette"]
            for state in palette:
                # print(state["Name"])

                if state["Name"].value == "minecraft:barrier":
                    has_barriers: bool = True

    # print("Has Barrier Blocks: %s" % has_barriers)
    return has_barriers


def main_single_player(world_folder: str):
    # TODO: Scan Player Inventories And Ender Chests

    nether_path: str = os.path.join(world_folder, "DIM-1")
    overworld_path: str = world_folder
    the_end_path: str = os.path.join(world_folder, "DIM1")
    custom_dimensions_path: str = os.path.join(world_folder, "dimensions")

    dimensions_to_scan: List[str] = [overworld_path]

    # If The Nether Exists, Add To The Scan List
    if os.path.exists(nether_path):
        dimensions_to_scan.append(nether_path)

    # If The End Exists, Add To The Scan List
    if os.path.exists(the_end_path):
        dimensions_to_scan.append(the_end_path)

    # If Custom Dimensions Exist, Add To The Scan List
    if os.path.exists(custom_dimensions_path):
        for namespace in os.listdir(custom_dimensions_path):
            namespace_path: str = os.path.join(custom_dimensions_path, namespace)
            if os.path.isfile(namespace_path):
                continue

            for dimension in os.listdir(namespace_path):
                dimension_path: str = os.path.join(namespace_path, dimension)
                if os.path.isfile(dimension_path):
                    continue

                # print(dimension_path)
                dimensions_to_scan.append(dimension_path)

    has_barriers: bool = False
    try:
        for dimension in dimensions_to_scan:
            try:
                world = WorldFolder(dimension)
            except nbt.world.UnknownWorldFormat:
                # E.g Empty World
                continue

            # For Retrieving The Right Dimension Name Regardless Of Trailing Slashes
            # TODO: Grab Actual In Game Dimension Names (Like With /execute in namespace:dimension_name) When Possible
            if dimension.endswith("/") or dimension.endswith("\\"):
                dimension_folder_name: str = os.path.basename(os.path.dirname(dimension))
            else:
                dimension_folder_name: str = os.path.basename(dimension)

            for chunk in world.iter_nbt():
                try:
                    # Check Block Entities
                    barriers = check_blocks(chunk=chunk, dimension=dimension_folder_name)

                    if barriers:
                        has_barriers: bool = True
                except UnicodeDecodeError as e:
                    # This won't catch the issue as the issue is in world.iter_nbt(), not check_storages(...)
                    # hermitcraft6 currently breaks the scanner. Docm77 Alien Tech Books Are To Blame
                    # TODO: See Bug Report With Patch For Fix: https://github.com/twoolie/NBT/issues/144
                    print("Failed To Read Chunk (%s, %s) Due To Invalid Data!!!" % ("x", "z"))
                    print("-" * 40)
                    print("Trace: %s" % e)
                    print("-" * 40)

            print("Has Barrier Blocks: %s" % has_barriers)
    except KeyboardInterrupt:
        return 3


# List Of Worlds To Test Against
# https://hermitcraft.fandom.com/wiki/Map_Downloads
# https://www.2b2t.online/wiki/World%20Downloads
# https://download.scicraft.net/
if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("No World Folder Specified!!!")
        sys.exit(1)

    world_folder_path: str = sys.argv[1]
    if not os.path.exists(world_folder_path):
        print("World Folder Does Not Exist!!!")
        sys.exit(2)

    sys.exit(main_single_player(world_folder=world_folder_path))
