extends CharacterBody3D
## Standalone model inspection; independent of multiplayer and project input actions.

@onready var camera: Camera3D = $Camera3D
@onready var collider: CollisionShape3D = $CollisionShape3D
@export var tour_enabled := true
@export var step_height := 0.28
@onready var spawn_transform := transform
var tour: Array[Vector3] = []
var tour_pause := 0.0
var crouched := false
var target_camera_y := 0.65
var target_height := 1.8

func _ready() -> void:
	DisplayServer.window_set_title("Home Alone — House Walkthrough")
	rotation = Vector3.ZERO
	camera.rotation = Vector3.ZERO
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	if "--tour" in OS.get_cmdline_user_args():
		start_tour()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * 0.002)
		camera.rotate_x(-event.relative.y * 0.002)
		camera.rotation.x = clampf(camera.rotation.x, -1.4, 1.4)
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		if event.keycode == KEY_R:
			reset_position()
		if event.keycode == KEY_T:
			start_tour()
		if event.keycode == KEY_C or event.keycode == KEY_CTRL:
			set_crouched(not crouched)
	if event is InputEventMouseButton and event.pressed:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func start_tour() -> void:
	if not tour_enabled:
		return
	set_crouched(false)
	position = Vector3(0, 1, 8)
	rotation = Vector3.ZERO
	camera.rotation = Vector3.ZERO
	velocity = Vector3.ZERO
	tour = [Vector3(0,0,-1.7), Vector3(-6.8,0,-1.7), Vector3(-6.8,0,-5),
		Vector3(-10,0,-5), Vector3(-6.8,0,-5), Vector3(-6.8,0,-1.7),
		Vector3(3,0,-1.7), Vector3(7,0,-1.7), Vector3(7,0,-9),
		Vector3(5,0,-9), Vector3(5,0,-16), Vector3(5,0,-9),
		Vector3(1,0,-9), Vector3(1,0,-1.7), Vector3(-1.05,0,-1.7),
		Vector3(-1.05,0,-9.1), Vector3(1.05,0,-9.1), Vector3(1.05,0,-2)]
	tour_pause = 1.0
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func set_crouched(value: bool) -> void:
	if crouched == value:
		return
	if not value and test_move(global_transform, Vector3.UP * (1.8 - collider.shape.height)):
		return
	crouched = value
	target_camera_y = 0.05 if crouched else 0.65
	target_height = 1.2 if crouched else 1.8

func reset_position() -> void:
	tour.clear()
	transform = spawn_transform
	camera.rotation = Vector3.ZERO
	velocity = Vector3.ZERO
	set_crouched(false)

func _physics_process(delta: float) -> void:
	var shape := collider.shape as CapsuleShape3D
	shape.height = move_toward(shape.height, target_height, delta * 3.0)
	# Keep the feet fixed while crouching; gravity owns world-space height.
	collider.position.y = (shape.height - 1.8) * 0.5
	camera.position.y = move_toward(camera.position.y, target_camera_y, delta * 3.0)
	if not tour.is_empty():
		var offset := tour[0] - position
		offset.y = 0
		if offset.length() < 0.14:
			tour.pop_front()
			tour_pause = 0.6
			velocity = Vector3.ZERO
			return
		tour_pause = maxf(0, tour_pause - delta)
		rotation.y = lerp_angle(rotation.y, atan2(-offset.x, -offset.z), minf(1, delta*4))
		var forward := offset.normalized() * (2.7 if tour_pause == 0 else 0.0)
		velocity = Vector3(forward.x, velocity.y - 9.8*delta, forward.z)
		move_with_steps(delta)
		return
	var direction := Vector3.ZERO
	if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		direction = Vector3(
			float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A)),
			0,
			float(Input.is_physical_key_pressed(KEY_S)) - float(Input.is_physical_key_pressed(KEY_W)))
	var movement_speed := 1.9 if crouched else (6.0 if Input.is_physical_key_pressed(KEY_SHIFT) else 3.5)
	var movement := basis * direction.normalized() * movement_speed
	velocity.x = movement.x
	velocity.z = movement.z
	velocity.y -= 9.8 * delta
	if is_on_floor() and Input.is_physical_key_pressed(KEY_SPACE) and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		velocity.y = 4.5
	move_with_steps(delta)
	if position.y < -10:
		reset_position()

func move_with_steps(delta: float) -> void:
	var motion := Vector3(velocity.x, 0, velocity.z) * delta
	if velocity.y <= 0 and not motion.is_zero_approx() and (is_on_floor() or test_move(global_transform, Vector3.DOWN * 0.05)) and test_move(global_transform, motion):
		var up := Vector3.UP * step_height
		var raised := global_transform
		raised.origin += up
		if not test_move(global_transform, up) and not test_move(raised, motion):
			raised.origin += motion
			var landing := KinematicCollision3D.new()
			# A capsule first touches a stair's corner with a slanted normal.
			if test_move(raised, -up, landing) and landing.get_normal().y > 0.1:
				position.y += step_height + landing.get_travel().y
	move_and_slide()
