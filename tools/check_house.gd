extends SceneTree
## godot --headless --path . --fixed-fps 60 --script tools/check_house.gd

var body: CharacterBody3D
var failures := 0

func _initialize() -> void:
	call_deferred("check")

func check() -> void:
	var house := load("res://assets/home_alone/home_alone_blockout.glb").instantiate() as Node3D
	root.add_child(house)
	var colliders := house.find_children("*", "CollisionShape3D", true, false)
	expect(colliders.size() > 100, "structural collision imported")
	for stair in ["MainStair", "AtticStair"]:
		var ramp := house.find_child(stair, true, false)
		expect(ramp is StaticBody3D, stair + " imports as collision-only ramp")
		if ramp:
			expect(ramp.find_children("*", "MeshInstance3D", true, false).is_empty(), "ramp is invisible")
	body = CharacterBody3D.new()
	body.floor_snap_length = 0.4
	var shape := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.5
	capsule.height = 1.8
	shape.shape = capsule
	body.add_child(shape)
	root.add_child(body)
	body.position = Vector3(0, 1, 8)
	await physics_frame
	# Entrance -> main stairs -> upper landing -> attic -> back down both flights.
	for point in [Vector3(0,0.9,-1.7), Vector3(-1.05,0.9,-1.7),
		Vector3(-1.05,4.3,-9.1), Vector3(1.05,4.3,-9.1), Vector3(1.05,7.7,-2),
		Vector3(1.05,4.3,-9.1), Vector3(-1.05,4.3,-9.1), Vector3(-1.05,0.9,-1.7),
		# Living and family wing, returning through foyer into dining, sunroom, kitchen.
		Vector3(-6.8,0.9,-1.7), Vector3(-6.8,0.9,-5), Vector3(-10,0.9,-5),
		Vector3(-6.8,0.9,-5), Vector3(-6.8,0.9,-1.7), Vector3(3,0.9,-1.7),
		Vector3(7,0.9,-1.7), Vector3(7,0.9,-5), Vector3(10,0.9,-5),
		Vector3(7,0.9,-5), Vector3(7,0.9,-9), Vector3(5,0.9,-9), Vector3(5,0.9,-12),
		Vector3(5,0.9,-17), Vector3(7.1,0.9,-17), Vector3(7.1,0.9,-19)]:
		await walk_to(point)
	# The same capsule must be blocked by a solid hall partition.
	body.position = Vector3(1,0.95,-4)
	body.velocity = Vector3.ZERO
	for i in range(60):
		await physics_frame
		body.velocity = Vector3(3,-1,0)
		body.move_and_slide()
	expect(body.position.x < 1.7, "solid wall blocks capsule")
	var collider_count := colliders.size()
	house.queue_free()
	body.queue_free()
	await process_frame
	var preview: Node3D = load("res://scenes/House_Blockout_Preview.tscn").instantiate()
	root.add_child(preview)
	var walker := preview.get_node("Player") as CharacterBody3D
	walker.call("start_tour")
	for frame in range(10000):
		await physics_frame
		if walker.get("tour").is_empty():
			break
	expect(walker.get("tour").is_empty() and walker.position.y > 7.5, "guided tour reaches attic")
	expect(preview.get_node("WorldEnvironment").environment.ambient_light_source == Environment.AMBIENT_SOURCE_COLOR,
		"interior ambient light uses assigned color")
	print("HOUSE CHECK: ", collider_count, " colliders; ", failures, " failures")
	preview.queue_free()
	quit(1 if failures else 0)

func walk_to(target: Vector3) -> void:
	for frame in range(600):
		await physics_frame
		var offset := target - body.position
		offset.y = 0
		if offset.length() < 0.12:
			expect(absf(body.position.y - target.y) < 0.22, "floor height at " + str(target))
			return
		var movement := offset.normalized() * 3.5
		body.velocity = Vector3(movement.x, body.velocity.y - 9.8/60.0, movement.z)
		body.move_and_slide()
	expect(false, "blocked before " + str(target) + "; stopped at " + str(body.position))

func expect(ok: bool, message: String) -> void:
	if not ok:
		failures += 1
		push_error(message)
