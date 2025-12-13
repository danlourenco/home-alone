extends CharacterBody3D

@export var role: String = "kevin"
@export var base_speed: float = 6.0
@export var sprint_multiplier: float = 1.3
@export var jump_velocity: float = 4.5
@export var mouse_sensitivity: float = 0.1

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var health: int = 100
var status_effects: Array = []
var current_slow: float = 1.0
var can_move: bool = true

@onready var head: Node3D = $Head
@onready var camera: Camera3D = $Head/Camera3D
@onready var ray: RayCast3D = $Head/Camera3D/RayCast3D

func _ready():
    Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
    if role == "kevin":
        base_speed = 7.0
    set_process(true)

func _process(_delta):
    _handle_mouse_look()
    if role == "kevin":
        _handle_trap_selection()
    _update_socket_prompt()

func _physics_process(delta):
    if not can_move:
        return
    var velocity_vec = velocity
    if not is_on_floor():
        velocity_vec.y -= gravity * delta
    var input_dir = Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    var direction = (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
    var target_speed = base_speed * current_slow
    if Input.is_action_pressed("sprint"):
        target_speed *= sprint_multiplier
    if direction:
        velocity_vec.x = direction.x * target_speed
        velocity_vec.z = direction.z * target_speed
    else:
        velocity_vec.x = move_toward(velocity_vec.x, 0, target_speed)
        velocity_vec.z = move_toward(velocity_vec.z, 0, target_speed)
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity_vec.y = jump_velocity
    velocity = velocity_vec
    move_and_slide()

func _handle_mouse_look():
    var mouse_motion = Input.get_last_mouse_velocity() * mouse_sensitivity * 0.01
    rotate_y(-mouse_motion.x)
    head.rotate_x(-mouse_motion.y)
    head.rotation_degrees.x = clamp(head.rotation_degrees.x, -80.0, 80.0)

func _update_socket_prompt():
    if not ray.is_colliding():
        MatchManager.set_socket_prompt("")
        return
    var collider = ray.get_collider()
    if collider is Node:
        var socket: Node = collider
        if socket is Node3D and socket.has_method("get_prompt"):
            var prompt = socket.get_prompt()
            if role == "kevin" and MatchManager.get_selected_trap() != "":
                prompt += " | Press E to place %s" % MatchManager.get_selected_trap()
            MatchManager.set_socket_prompt(prompt)
            if role == "kevin" and Input.is_action_just_pressed("interact"):
                _attempt_place_trap(socket)
        else:
            MatchManager.set_socket_prompt("")

func _handle_trap_selection():
    if Input.is_action_just_pressed("trap_slot_1"):
        MatchManager.set_selected_trap_by_index(0)
    elif Input.is_action_just_pressed("trap_slot_2"):
        MatchManager.set_selected_trap_by_index(1)
    elif Input.is_action_just_pressed("trap_slot_3"):
        MatchManager.set_selected_trap_by_index(2)
    elif Input.is_action_just_pressed("trap_slot_4"):
        MatchManager.set_selected_trap_by_index(3)

func _attempt_place_trap(socket: Node):
    if not socket or not socket.has_method("has_trap"):
        return
    if socket.has_trap():
        return
    var trap_name = MatchManager.get_selected_trap()
    if trap_name == "":
        return
    if not MatchManager.can_afford(trap_name):
        MatchManager.set_socket_prompt("Not enough budget for %s" % trap_name)
        return
    Net.request_place_trap(socket.get_path(), trap_name)

func apply_trap_effect(data: Dictionary):
    if data.has("damage"):
        health -= int(data.get("damage", 0))
    var status = data.get("status", "")
    if status != "":
        current_slow = data.get("slow", 1.0)
        can_move = status != "stun"
        var duration = data.get("duration", 0.0)
        _start_status_timer(status, duration)

func _start_status_timer(name: String, duration: float):
    var timer = Timer.new()
    timer.one_shot = true
    timer.wait_time = duration
    add_child(timer)
    timer.timeout.connect(_clear_status)
    timer.start()

func _clear_status():
    current_slow = 1.0
    can_move = true
