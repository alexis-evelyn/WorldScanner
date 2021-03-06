import os
import sys
import uuid
import pandas as pd
from typing import List, Optional

import nbt
from nbt.world import WorldFolder

# The Purpose Of This Script Is To Help Me Determine What Items Need To Be Sorted In My SSP
# It's Not Meant For General Public Use

total_item_list: dict = {}


def check_block_entities(chunk: nbt.chunk, dimension: str):
    # The author themselves' mentioned just looking up the data myself and not using nbt.chunk.Chunk
    chunk_data: nbt.nbt = chunk["Level"]
    chunk_status: Optional[str] = None

    # Cause Apparently 2b2t World Downloads Have Some Tags Missing
    if "Status" in chunk_data:
        chunk_status: str = chunk_data["Status"]

    # If Not full, chunk is not fully generated yet and can be ignored for illegal item searching
    if chunk_status is not None and chunk_status.value.strip() != "full":
        return

    for entity in chunk_data["TileEntities"]:
        be_id: str = entity["id"].value
        x, y, z = entity["x"].value, entity["y"].value, entity["z"].value

        # Check Storages With `Items` tag
        check_storages(be_id=be_id, entity=entity, x=x, y=y, z=z, dimension=dimension)


# https://minecraft.fandom.com/wiki/Chunk_format
def check_storages(be_id: str, entity: nbt.nbt, x: int, y: int, z: int, dimension: str):
    # https://minecraft.fandom.com/wiki/Chunk_format#Block_entity_format
    if "Items" in entity and len(entity["Items"]) > 0:
        # This Code Works, I Just Hid It So I Don't See Coords
        print("%s - (%s, %s, %s) - %s" % (be_id, x, y, z, dimension))

        # print("%s" % be_id)
        print("-" * 40)

        if "CustomName" in entity:
            print("Custom Name: %s" % entity["CustomName"])

        items: nbt.nbt = entity["Items"]
        if "Items" in items:
            # TechReborn Based Block Entities Are Weird
            # See Items.Items[]
            items: nbt.nbt = items["Items"]

        tr_storage_unit_count: Optional[int] = None
        if "totalStoredAmount" in entity:
            tr_storage_unit_count: int = int(entity["totalStoredAmount"].value)

        for item in items:
            # Modify Item Count So It Represents TechReborn Storage Units
            # Only Slot 1 (Output Slot) Counts For The Total Storage Units.
            #     Slot 0 (Input Slot) Doesn't Count, Even If It Has Items In It
            if tr_storage_unit_count is not None and int(item["Slot"].value) == 1:
                item["Count"].value = tr_storage_unit_count

            # Todo: Add Means Of Recursively Findings Contents of Shulkers In Chests (Even Chests With NBT Data)
            #     Make sure to have a limit on the recursion, so check what the vanilla limit is.
            #     Also make sure to account for bundles too.
            # ...

            # We Want To Display The Embedded Storage First, Then The Items Inside
            # TODO: Note: This Isn't Recursive, So Won't Display Bundles In Bundles Or Bundles In Shulker Boxes
            print_item(item=item)
            add_item(item=item)
            if "tag" in item and "BlockEntityTag" in item["tag"] and "Items" in item["tag"]["BlockEntityTag"] and len(item["tag"]["BlockEntityTag"]["Items"]) > 0:
                # Shulker Boxes
                print("-"*20)
                for embedded_item in item["tag"]["BlockEntityTag"]["Items"]:
                    print_item(item=embedded_item)

                    # To Take Care Of Stacked Shulker Boxes (e.g. in TR Storage Units)
                    if int(item["Count"].value) > 1:
                        embedded_item["Count"].value = int(embedded_item["Count"].value) * int(item["Count"].value)

                    add_item(item=embedded_item)
                print("-"*20)
            elif "tag" in item and "Items" in item["tag"] and len(item["tag"]["Items"]) > 0:
                # Bundles
                print("-"*20)
                for embedded_item in item["tag"]["Items"]:
                    print_item(item=embedded_item)

                    # To Take Care Of Stacked Bundles (e.g. in TR Storage Units)
                    if int(item["Count"].value) > 1:
                        embedded_item["Count"].value = int(embedded_item["Count"].value) * int(item["Count"].value)

                    add_item(item=embedded_item)
                print("-"*20)

        print("-" * 40)
        print(" ")


def add_item(item: nbt.nbt):
    # Block Entity Names Used To Not Be Prefixed With "minecraft:". E.g. Chest instead of minecraft:chest
    # Block Entities Could Still Have The Item ID System - https://minecraft-ids.grahamedgecombe.com/

    if str(item["id"].value) in total_item_list:
        total_item_list[str(item["id"].value)]["Count"] += int(item["Count"].value)
    else:
        total_item_list[str(item["id"].value)] = {}
        total_item_list[str(item["id"].value)]["Count"] = int(item["Count"].value)


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
                    check_block_entities(chunk=chunk, dimension=dimension_folder_name)
                except UnicodeDecodeError as e:
                    # This won't catch the issue as the issue is in world.iter_nbt(), not check_storages(...)
                    # hermitcraft6 currently breaks the scanner. Docm77 Alien Tech Books Are To Blame
                    # TODO: See Bug Report With Patch For Fix: https://github.com/twoolie/NBT/issues/144
                    print("Failed To Read Chunk (%s, %s) Due To Invalid Data!!!" % ("x", "z"))
                    print("-" * 40)
                    print("Trace: %s" % e)
                    print("-" * 40)

        df = pd.DataFrame.from_dict(total_item_list, orient="index")
        df.index.name = "Item ID"
        df.sort_values(axis=0, ascending=False, inplace=True, by=["Count"])
        df["Total"] = df["Count"].sum()
        print("-"*100)
        print(df)
        df.to_csv(os.path.join(world_folder, "total_item_list.csv"))
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
