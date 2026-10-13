extends SceneTree
## Godot --headless --path . --fixed-fps 60 --script tools/check_online_walkthrough.gd

var failures := 0
var player: CharacterBody3D

func _initialize() -> void:
	call_deferred("check")

func check() -> void:
	var scene := load("res://scenes/Online_Home_Alone_Walkthrough.tscn").instantiate() as Node3D
	root.add_child(scene)
	player = scene.get_node("Player")
	player.set_physics_process(false)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	await physics_frame
	var colliders := scene.get_node("House").find_children("*", "CollisionShape3D", true, false)
	expect(colliders.size() == 273, "309 imported meshes minus 36 door parts have collision")
	var route := [Vector3(1.9,0,7), Vector3(1.9,0,3.2), Vector3(1.9,0,0),
		Vector3(2.7,0,-4), Vector3(3.3,0,-8), Vector3(6.5,0,-8),
		Vector3(9,0,-8), Vector3(9,0,-12), Vector3(11,0,-14), Vector3(11,0,-16)]
	for point in route:
		await walk_to(point)
	expect(absf(player.position.y - 2.21) < 0.1, "player reaches the raised kitchen floor")
	var resting_y := player.position.y
	player.call("set_crouched", true)
	for frame in range(30):
		await tick()
	expect(absf(player.position.y - resting_y) < 0.03, "crouching preserves floor height")
	expect(is_equal_approx(player.get_node("CollisionShape3D").shape.height, 1.2), "crouch capsule contracts")
	player.call("set_crouched", false)
	for frame in range(30):
		await tick()
	expect(is_equal_approx(player.get_node("CollisionShape3D").shape.height, 1.8), "capsule returns to standing height")
	player.velocity.y = 4.5
	var peak := resting_y
	for frame in range(90):
		await tick()
		peak = maxf(peak, player.position.y)
	expect(peak > resting_y + 0.7, "jump is not pulled toward a fixed world height")
	expect(absf(player.position.y - resting_y) < 0.03, "jump lands on the kitchen floor")
	expect(player.test_move(Transform3D(Basis.IDENTITY, Vector3(3.8,2.22,-5)), Vector3(2,0,0)),
		"solid foyer wall remains collidable")
	if "--capture" in OS.get_cmdline_user_args():
		player.rotation.y = -PI / 2
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://art/home_alone/online_kitchen_walkthrough.png")
	route.reverse()
	for point in route:
		await walk_to(point)
	await walk_to(Vector3(1.9,0,10))
	expect(absf(player.position.y - 1.036) < 0.1, "player descends front stairs onto the path")
	player.call("reset_position")
	expect(player.position.is_equal_approx(Vector3(1.9,2.2,0)), "reset uses imported scene spawn")
	player.call("start_tour")
	expect(player.get("tour").is_empty(), "old blockout tour is disabled in imported scene")
	print("ONLINE WALKTHROUGH CHECK: ", colliders.size(), " colliders; ", failures, " failures")
	quit(1 if failures else 0)

func tick() -> void:
	await physics_frame
	player._physics_process(1.0 / 60)

func walk_to(target: Vector3) -> void:
	for frame in range(600):
		await physics_frame
		var offset := target - player.position
		offset.y = 0
		if offset.length() < 0.12:
			return
		player.velocity = offset.normalized() * 3.5 + Vector3(0, player.velocity.y - 9.8 / 60, 0)
		player.move_with_steps(1.0 / 60)
	expect(false, "blocked before " + str(target) + "; stopped at " + str(player.position))

func expect(ok: bool, message: String) -> void:
	if not ok:
		failures += 1
		push_error(message)
