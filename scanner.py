import os
import sys
from typing import List, Optional

import nbt
from nbt.world import WorldFolder


def check_block_entities(chunk: nbt.chunk, dimension: str):
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

    # TileEntities (Block Entities), Entities, Sections (Blocks, A Bit Complicated)
    # Starting In 1.17, Entities Won't Exist In This File Once A Chunk Is Fully Generated
    # TODO: Scan For Items, Mules, Donkeys, Horses (E.g. mobs with inventory),
    #   Minecart Chests/Furnaces, Regular Chests, Trapped Chests, Furnaces, Blast Furnaces,
    #   Lecterns, Hoppers, Etc...

    # TODO: (1463, 201, 1337) - Find Out Where The Illegal Sword's Gone
    for entity in chunk_data["TileEntities"]:
        be_id: str = entity["id"].value
        x, y, z = entity["x"].value, entity["y"].value, entity["z"].value

        # TODO:
        #   * Determine Where To Stick Blocks Which Have PowerAcceptor.energy and Items
        #   * Figure Out Where To Stick totalStoredAmount And Items
        #   * Figure Out Where To Stick TankStorage and Items

        # Check Storages With `Items` tag
        check_storages(be_id=be_id, entity=entity, x=x, y=y, z=z, dimension=dimension)

        # Check Lecterns
        check_lecterns(be_id=be_id, entity=entity, x=x, y=y, z=z, dimension=dimension)

        # Check Jukeboxes
        check_jukeboxes(be_id=be_id, entity=entity, x=x, y=y, z=z, dimension=dimension)

        # Check Signs
        check_signs(be_id=be_id, entity=entity, x=x, y=y, z=z, dimension=dimension)


def check_signs(be_id: str, entity: nbt.nbt, x: int, y: int, z: int, dimension: str):
    if be_id == "minecraft:sign":
        if "Text1" not in entity:
            print("%s - (%s, %s, %s) - %s" % (be_id, x, y, z, dimension))
            print("-" * 40)
            print("Cannot Read Pre-1.8 Signs!!! Skipping For Now!!!")
            print("-" * 40)
            return

        glowing: bool = False

        if "GlowingText" in entity:
            glowing: bool = entity["GlowingText"]

        # What Version Was Color Added?
        color: str = entity["Color"]

        # Text1-4 Had Been Added In 1.8
        # TODO: Make Sure To Check If This Exists (Versus Old Style Of NBT Data)
        line_one: str = entity["Text1"]
        line_two: str = entity["Text2"]
        line_three: str = entity["Text3"]
        line_four: str = entity["Text4"]

        print("%s - (%s, %s, %s) - %s" % (be_id, x, y, z, dimension))
        print("-" * 40)
        print("Glowing: %s" % glowing)
        print("Color: %s" % color)
        print("Line 1: %s" % line_one)
        print("Line 2: %s" % line_two)
        print("Line 3: %s" % line_three)
        print("Line 4: %s" % line_four)
        print("-" * 40)
        print(" ")


def check_lecterns(be_id: str, entity: nbt.nbt, x: int, y: int, z: int, dimension: str):
    if be_id == "minecraft:lectern":
        book: Optional[nbt.nbt] = None
        page: Optional[int] = None

        if "Book" in entity:
            book: nbt.nbt = entity["Book"]

        if "Page" in entity:
            page: int = entity["Page"]

        # Check For Book Item
        if book is not None:
            print("%s - (%s, %s, %s) - %s" % (be_id, x, y, z, dimension))
            print("-" * 40)
            print_item(item=book)  # Lecterns Don't Have A Slot Tag

        # Check For Page Tag Separately In Case It Doesn't Exist
        if page is not None:
            print("Page: %s" % page)

        print("-" * 40)
        print(" ")


def check_jukeboxes(be_id: str, entity: nbt.nbt, x: int, y: int, z: int, dimension: str):
    # What's With The `Record` Tag Pre-1.13?
    if be_id == "minecraft:jukebox":
        record: Optional[nbt.nbt] = None

        if "RecordItem" in entity:
            record: nbt.nbt = entity["RecordItem"]

            print("%s - (%s, %s, %s) - %s" % (be_id, x, y, z, dimension))
            print("-" * 40)
            print_item(item=record)  # Jukeboxes Don't Have A Slot Tag
            print("-" * 40)
            print(" ")


# https://minecraft.fandom.com/wiki/Chunk_format
def check_storages(be_id: str, entity: nbt.nbt, x: int, y: int, z: int, dimension: str):
    # if "LootTableSeed" in entity:
    #     print("%s - (%s, %s, %s) - %s" % (be_id, x, y, z, dimension))
    #     print("-" * 40)
    #     print("Loot Table: %s" % entity["LootTable"])
    #     print("Loot Table Seed: %s" % entity["LootTableSeed"])
    #     print("-" * 40)
    #     print(" ")

    # https://minecraft.fandom.com/wiki/Chunk_format#Block_entity_format
    if "Items" in entity and len(entity["Items"]) > 0:
        print("%s - (%s, %s, %s) - %s" % (be_id, x, y, z, dimension))
        print("-" * 40)

        if "CustomName" in entity:
            print("Custom Name: %s" % entity["CustomName"])

        items: nbt.nbt = entity["Items"]
        if "Items" in items:
            # TechReborn Based Block Entities Are Weird
            # See Items.Items[]
            items: nbt.nbt = items["Items"]

        for item in items:
            print_item(item=item)

        print("-" * 40)
        print(" ")


def print_item(item: nbt.nbt):
    # Block Entity Names Used To Not Be Prefixed With "minecraft:". E.g. Chest instead of minecraft:chest
    # Block Entities Could Still Have The Item ID System - https://minecraft-ids.grahamedgecombe.com/
    # TODO: Make Something Cleaner Than Nested If Statements And Copied Messages
    if "Slot" in item:
        if "tag" in item:
            print("%s - Slot: %s - Count: %s - Tag: %s" % (item["id"], item["Slot"], item["Count"], item["tag"]))
        else:
            print("%s - Slot: %s - Count: %s" % (item["id"], item["Slot"], item["Count"]))
    else:
        if "tag" in item:
            print("%s - Count: %s - Tag: %s" % (item["id"], item["Count"], item["tag"]))
        else:
            print("%s - Count: %s" % (item["id"], item["Count"]))


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
                    check_block_entities(chunk=chunk, dimension=dimension)

                    # Check Entities (Behavior Is Different Starting In 1.17)
                    # ...

                    # Check Player Inventories
                    # ...

                    # Check Player Ender Chests
                    # ...
                except UnicodeDecodeError as e:
                    # This won't catch the issue as the issue is in world.iter_nbt(), not check_storages(...)
                    # hermitcraft6 currently breaks the scanner. Docm77 Alien Tech Books Are To Blame
                    # TODO: See Bug Report With Patch For Fix: https://github.com/twoolie/NBT/issues/144
                    print("Failed To Read Chunk (%s, %s) Due To Invalid Data!!!" % ("x", "z"))
                    print("-" * 40)
                    print("Trace: %s" % e)
                    print("-" * 40)
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
