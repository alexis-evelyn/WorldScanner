import os
import sys
from typing import List

import nbt
from nbt.world import WorldFolder


# https://minecraft.fandom.com/wiki/Chunk_format
def check_storages(chunk: nbt.chunk, dimension: str):
    # TODO: Look Up Chunk Version Differences And Create Handlers
    #   For Each Of The Differences (Then Abstract The Data To My Own Format)
    chunk_version: int = chunk["DataVersion"]

    # The author themselves' mentioned just looking up the data myself and not using nbt.chunk.Chunk
    chunk_data: nbt.nbt = chunk["Level"]
    chunk_status: str = chunk_data["Status"]

    # In Chunks From Origin (0, 0, 0)
    x_pos: int = chunk_data["xPos"]
    z_pos: int = chunk_data["zPos"]

    # print(f"Dimension: %s - Chunk (%s, %s)" % (dimension, x_pos, z_pos))

    # If Not full, chunk is not fully generated yet and can be ignored for illegal item searching
    if chunk_status.value.strip() != "full":
        return

    # TileEntities (Block Entities), Entities, Sections (Blocks, A Bit Complicated)
    # TODO: Scan For Items, Mules, Donkeys, Horses (E.g. mobs with inventory),
    #   Minecart Chests/Furnaces, Regular Chests, Trapped Chests, Furnaces, Blast Furnaces,
    #   Lecterns, Hoppers, Etc...

    # TODO: (1463, 201, 1337) - Find Out Where The Illegal Sword's Gone
    for entity in chunk_data["TileEntities"]:
        id: str = entity["id"].value
        x, y, z = entity["x"].value, entity["y"].value, entity["z"].value

        # https://minecraft.fandom.com/wiki/Chunk_format#Block_entity_format
        if "Items" in entity and len(entity["Items"]) > 0:
            print("%s - (%s, %s, %s) - %s" % (id, x, y, z, dimension))
            print("-"*40)
            for item in entity["Items"]:
                if id.startswith("minecraft:"):
                    if "tag" in item:
                        print("%s - Slot: %s - Count: %s - Tag: %s" % (item["id"], item["Slot"], item["Count"], item["tag"]))
                    else:
                        print("%s - Slot: %s - Count: %s" % (item["id"], item["Slot"], item["Count"]))
                else:
                    # TODO: Read Modded Such As TechReborn and RandomTech Without Crashing
                    #   This involves checking the NBT Data In Game To See What I Should Expect
                    print("Modded - %s" % item)
            print("-"*40)
            print(" ")


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
        dimensions_to_scan.append(nether_path)

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

    try:
        for dimension in dimensions_to_scan:
            try:
                world = WorldFolder(dimension)
            except nbt.world.UnknownWorldFormat:
                # E.g Empty World
                continue

            # For Retrieving The Right Dimension Name Regardless Of Trailing Slashes
            if dimension.endswith("/") or dimension.endswith("\\"):
                dimension_folder_name: str = os.path.basename(os.path.dirname(dimension))
            else:
                dimension_folder_name: str = os.path.basename(dimension)

            for chunk in world.iter_nbt():
                check_storages(chunk=chunk, dimension=dimension_folder_name)
    except KeyboardInterrupt:
        return 3


def main(world_folder: str):
    world = WorldFolder(world_folder)

    try:
        for chunk in world.iter_nbt():
            check_storages(chunk=chunk, dimension=os.path.basename(world_folder))
    except KeyboardInterrupt:
        return 3


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("No World Folder Specified!!!")
        sys.exit(1)

    world_folder_path: str = sys.argv[1]
    if not os.path.exists(world_folder_path):
        print("World Folder Does Not Exist!!!")
        sys.exit(2)

    sys.exit(main_single_player(world_folder=world_folder_path))
