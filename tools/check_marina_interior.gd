extends SceneTree

var failures := 0
var player: CharacterBody3D

func _initialize() -> void:
	call_deferred("check")

func check() -> void:
	var scene := load("res://scenes/Marina_House_Walkthrough.tscn").instantiate() as Node3D
	root.add_child(scene)
	player = scene.get_node("Player") as CharacterBody3D
	player.set_physics_process(false)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	await physics_frame
	var meshes := scene.get_node("House").find_children("*", "MeshInstance3D", true, false)
	var collisions := scene.get_node("House").find_children("*", "CollisionShape3D", true, false)
	expect(meshes.size() > 250, "Marina asset has structural and dressing meshes")
	expect(collisions.size() > 80, "fixed room geometry has imported collision")
	var expected := ["Foyer", "Living", "Den", "Dining", "Breakfast", "Kitchen", "Ceilings"]
	for prefix in expected:
		var found := false
		for node in meshes:
			if String(node.name).begins_with(prefix):
				found = true
				break
		expect(found, "room group exists: " + prefix)
	for frame in range(30):
		await physics_frame
		player._physics_process(1.0 / 60)
	expect(player.is_on_floor() and absf(player.position.y - 0.9) < 0.05, "spawn settles on foyer floor")
	# Blender (x,y,z) imports as Godot (x,z,-y). Walk continuously, without teleporting.
	var route := [Vector3(1.15,0.9,-7.75), Vector3(1.15,0.9,-9.55),
		Vector3(3.8,0.9,-9.55), Vector3(2.95,0.9,-9.85),
		Vector3(3.8,0.9,-9.55), Vector3(1.15,0.9,-9.55),
		Vector3(1.15,0.9,-7.75), Vector3(1.15,0.9,-2.7),
		Vector3(-6.8,0.9,-2.7), Vector3(-9.45,0.9,-2.7),
		Vector3(-9.45,0.9,-6.7), Vector3(-9.45,0.9,-2.7),
		Vector3(1.15,0.9,-2.7), Vector3(2.8,0.9,-2.7),
		Vector3(2.8,0.9,-5.8), Vector3(3.5,0.9,-5.8),
		Vector3(3.5,0.9,-7.2), Vector3(3.5,0.9,-7.35),
		Vector3(7.4,0.9,-7.35), Vector3(7.4,0.9,-11.5),
		Vector3(6.8,0.9,-11.5), Vector3(6.8,0.9,-13.5),
		Vector3(6.8,0.9,-17.3), Vector3(9.98,0.9,-17.3),
		Vector3(9.98,0.9,-11.6)]
	for point in route:
		if not await walk_to(point):
			break
	if failures == 0:
		route.reverse()
		for point in route:
			if not await walk_to(point):
				break
	var space := scene.get_world_3d().direct_space_state
	for point in [Vector3(-3,4.8,-6), Vector3(3,4.8,-6), Vector3(0,4.8,-2), Vector3(0,8,-6)]:
		expect(not space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(0,4.8,-6), point)).is_empty(), "upper foyer enclosed toward " + str(point))
	for point in [Vector3(1,4.5,-12), Vector3(4.5,4.5,-12), Vector3(2.92,4.5,-9.5), Vector3(2.92,4.5,-15), Vector3(2.92,6,-12)]:
		expect(not space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(2.92,4.5,-12), point)).is_empty(), "service stair enclosed toward " + str(point))
	for node in meshes:
		if String(node.name).begins_with("Kitchen_Island long counter"):
			var bounds: AABB = node.global_transform * node.get_aabb()
			expect(bounds.end.y >= 0.90 and bounds.end.y <= 0.93, "island worktop is human scale")
	expect(player.test_move(Transform3D(Basis.IDENTITY, Vector3(1.1,0.91,-5)), Vector3(2,0,0)), "foyer partition blocks player")
	expect(player.test_move(Transform3D(Basis.IDENTITY, Vector3(7.3,0.91,-14.6)), Vector3(2,0,0)), "island blocks player")
	player.call("reset_position")
	expect(player.position.is_equal_approx(Vector3(0,1,-1.9)), "reset returns to clear foyer spawn")
	if "--capture" in OS.get_cmdline_user_args():
		var camera := Camera3D.new()
		scene.add_child(camera)
		camera.current = true
		camera.fov = 78
		scene.get_node("CanvasLayer").hide()
		for view in [
			["foyer", Vector3(1.15,1.55,-2.7), Vector3(-0.6,1.5,-6)],
			["den", Vector3(-9.45,1.55,-2.7), Vector3(-10.2,1.3,-5.7)],
			["dining", Vector3(2.8,1.55,-5.8), Vector3(5,1.0,-3.2)],
			["breakfast", Vector3(7.4,1.55,-7.35), Vector3(2.6,1.5,-9.4)],
			["kitchen", Vector3(6.8,1.55,-13.5), Vector3(9.5,1.3,-17)],
			["kitchen-reverse", Vector3(9.98,1.55,-17.3), Vector3(7,1.3,-11.5)]]:
			camera.position = view[1]
			camera.look_at(view[2])
			for frame in range(5):
				await process_frame
			await RenderingServer.frame_post_draw
			expect(root.get_texture().get_image().save_png("res://art/home_alone/marina/godot-" + view[0] + ".png") == OK, "capture " + view[0])
	print("MARINA INTERIOR CHECK: ", meshes.size(), " meshes; ", collisions.size(), " colliders; ", failures, " failures")
	quit(1 if failures else 0)

func walk_to(target: Vector3) -> bool:
	for frame in range(600):
		await physics_frame
		var offset := target - player.position
		offset.y = 0
		if offset.length() < 0.12:
			expect(absf(player.position.y - target.y) < 0.08, "floor height at " + str(target))
			return true
		player.velocity = offset.normalized() * 3.5 + Vector3(0, player.velocity.y - 9.8 / 60, 0)
		player.move_with_steps(1.0 / 60)
	expect(false, "blocked before " + str(target) + "; stopped at " + str(player.position))
	return false

func expect(ok: bool, message: String) -> void:
	if not ok:
		failures += 1
		push_error(message)
