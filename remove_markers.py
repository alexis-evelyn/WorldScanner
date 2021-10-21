import os
import sys
from typing import List, Optional

import nbt
from nbt.world import WorldFolder
from nbt.nbt import TAG, TAG_Int


def check_entities(chunk: nbt.chunk, dimension: str, folder: str):
    chunk_data: nbt.nbt = {}
    pre_format_change: bool = True
    if "Level" in chunk:
        # Pre-1.17 Entity Storage
        chunk_data: nbt.nbt = chunk["Level"]
    elif "Entities" in chunk:
        # 1.17+ Entity Storage
        chunk_data: nbt.nbt = chunk
        pre_format_change: bool = False

    if "Entities" in chunk_data:
        entities_to_remove: List[TAG] = []
        for entity in chunk_data["Entities"]:
            e_id: str = entity["id"].value
            x, y, z = entity["Pos"]

            # Temporarily Block All Non-Markers From The Entity Output List
            if e_id != "minecraft:marker":
                continue
            entities_to_remove.append(entity)

            print("%s - (%s, %s, %s) - %s" % (e_id, x, y, z, dimension))
            print("-" * 40)

            # Markers Are Meant For Datapacks To Be Able To Store NBT Data
            if e_id == "minecraft:marker":
                print("Data: %s" % entity["data"])

            # TODO: Parse UUID To 32 Character Hex String (Format Changes In 1.16)
            #   See: https://minecraft.fandom.com/wiki/Universally_unique_identifier
            # Check If UUID Exists (hermitcraft7 has a turtle that doesn't have a UUID)
            e_uuid: Optional[str] = None
            if "UUID" in entity:
                e_uuid: str = entity["UUID"]

            print("UUID: %s" % e_uuid)
            print("-" * 40)
            print(" ")

        # Don't Bother Copying Chunks Which Weren't Modified
        if len(entities_to_remove) == 0:
            # I could use an optional and check that, but I'm lazy tonight
            # I also don't need to return pre_format_change cause I run two for loops to check both versions of data,
            #   however, I kept it in for debugging purposes.
            return False, pre_format_change, chunk

        for entity in entities_to_remove:
            # Note: This code does not verify these NBT Keys Exist
            print("Removing %s With UUID %s" % (entity["id"].value, entity["UUID"]))
            chunk_data["Entities"].remove(entity)

        # print(chunk_data.pretty_tree())

        if pre_format_change:
            chunk = chunk_data
        else:
            chunk["Level"] = chunk_data

        return True, pre_format_change, chunk
    return False, pre_format_change, chunk


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

            # For Creating Temporary Storage Of Modified Entity List (1.16-)
            # if not os.path.exists(os.path.join(dimension, "temp_region")):
            #     os.makedirs(os.path.join(dimension, "temp_region"))

            # For Creating Temporary Storage Of Modified Entity List (1.17+)
            # if not os.path.exists(os.path.join(dimension, "temp_entities")):
            #     os.makedirs(os.path.join(dimension, "temp_entities"))

            for region in world.iter_regions():
                modified_chunks: List[nbt.nbt] = []
                for chunk in region.iter_chunks():
                    try:
                        # Check Entities (Behavior Is Different Starting In 1.17)
                        was_modified, pre_format_change, modified_chunk = check_entities(chunk=chunk, dimension=dimension_folder_name, folder=dimension)

                        if was_modified:
                            modified_chunks.append(chunk)
                    except UnicodeDecodeError as e:
                        # This won't catch the issue as the issue is in world.iter_nbt(), not check_storages(...)
                        # hermitcraft6 currently breaks the scanner. Docm77 Alien Tech Books Are To Blame
                        # TODO: See Bug Report With Patch For Fix: https://github.com/twoolie/NBT/issues/144
                        print("Failed To Read Chunk (%s, %s) Due To Invalid Data!!!" % ("x", "z"))
                        print("-" * 40)
                        print("Trace: %s" % e)
                        print("-" * 40)

                # Untested
                if len(modified_chunks) > 0:
                    for chunk in modified_chunks:
                        chunk_data: nbt.nbt = chunk["Level"]
                        x_pos: TAG_Int = chunk_data["xPos"]
                        z_pos: TAG_Int = chunk_data["zPos"]

                        region.write_chunk(x=x_pos.value, z=z_pos.value, nbt_file=chunk)

            # Region File Name - For Grabbing Entities From Entities Folder If It Exists (Post 1.17)
            entity_files_path: str = os.path.join(dimension, "entities")
            if os.path.exists(entity_files_path):
                entity_region_file_names: List[str] = os.listdir(entity_files_path)
                entity_region_file_list: List[str] = []
                for region_file in entity_region_file_names:
                    if region_file.endswith(".mca"):
                        entity_region_file_list.append(os.path.join(entity_files_path, region_file))

                world.set_regionfiles(entity_region_file_list)

            for region in world.iter_regions():
                modified_chunks: List[nbt.nbt] = []
                for chunk in region.iter_chunks():
                    try:
                        # Check Entities (Behavior Is Different Starting In 1.17)
                        was_modified, pre_format_change, modified_chunk = check_entities(chunk=chunk, dimension=dimension_folder_name, folder=dimension)

                        if was_modified:
                            modified_chunks.append(chunk)
                    except UnicodeDecodeError as e:
                        # This won't catch the issue as the issue is in world.iter_nbt(), not check_storages(...)
                        # hermitcraft6 currently breaks the scanner. Docm77 Alien Tech Books Are To Blame
                        # TODO: See Bug Report With Patch For Fix: https://github.com/twoolie/NBT/issues/144
                        print("Failed To Read Chunk (%s, %s) Due To Invalid Data!!!" % ("x", "z"))
                        print("-" * 40)
                        print("Trace: %s" % e)
                        print("-" * 40)

                if len(modified_chunks) > 0:
                    # Turns Out I Don't Need To Write The Region File Myself
                    #   So, This Commented Out Code Is Useless Code Now
                    # r.-1.0.mca
                    # region_file_name: str = "r.%s.%s.mca" % (region.loc.x, region.loc.z)
                    # region_file_path: str = os.path.join(dimension, "temp_entities", region_file_name)
                    # print("Saving Modified Region File To: %s" % region_file_path)

                    for chunk in modified_chunks:
                        # print(chunk.pretty_tree())
                        chunk_data: nbt.nbt = chunk["Position"]

                        # Cause For Reasons, The Int Array Is An Actual Int And Not An Int Tag
                        x_pos: int = chunk_data[0]
                        z_pos: int = chunk_data[1]

                        # Causes Infinite Recursion Loop For Some Reason, Makes It Impossible To Edit Chunks
                        # TODO: Figure Out What To Do About: https://github.com/twoolie/NBT/blob/b735d465d198965e7347d24493bfe2e4e30fe39a/nbt/nbt.py#L703
                        # region.write_chunk(x=x_pos, z=z_pos, nbt_file=chunk)

                    # print(region.pretty_tree())
                    # region.write_file(region_file_path)
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