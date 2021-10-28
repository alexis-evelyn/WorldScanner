# data get storage cleanup:marker current_dimension
# data get storage cleanup:marker current_block_x
# data get storage cleanup:marker current_block_z

# execute in %s run kill @e[type=minecraft:marker]
# execute in %s run forceload remove %s %s

# We Can't Have Variables In Datapacks Yet, So We Have To Load All Chunks At Once And Then Delete All Markers At Once
kill @e[type=minecraft:marker]