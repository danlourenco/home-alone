extends Node

@onready var house: Node3D = $"../House"

func _ready() -> void:
	# Imported door assemblies are leaf, frame, handle. Leave frames in place.
	# Hide the leaves/handles so open doors cannot obstruct another narrow passage.
	var doors := [2925, 2929, 2933, 2937, 2941, 2957, 2961, 2965,
		2969, 2973, 2977, 2981, 2985, 2989, 2993, 2997, 3001, 3005]
	for door in doors:
		for part in [door, door + 2]:
			house.get_node("object%d" % part).hide()
	for node in house.find_children("*", "MeshInstance3D", true, false):
		var mesh := node as MeshInstance3D
		if mesh.mesh and mesh.is_visible_in_tree() and mesh.find_children("*", "StaticBody3D", false, false).is_empty():
			mesh.create_trimesh_collision()
