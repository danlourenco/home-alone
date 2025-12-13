extends Node3D

@export var trap_name: String = "Trap"
@export var cost: int = 10
@export var damage: int = 0
@export var status_effect: String = ""
@export var status_duration: float = 0.0
@export var slow_multiplier: float = 1.0
var armed: bool = true

func _ready():
    for child in get_children():
        if child is Area3D:
            child.body_entered.connect(_on_body_entered)

func _on_body_entered(body: Node) -> void:
    if not armed:
        return
    if not multiplayer.is_server():
        return
    if not body.has_method("apply_trap_effect"):
        return
    armed = false
    body.apply_trap_effect({
        "name": trap_name,
        "damage": damage,
        "status": status_effect,
        "duration": status_duration,
        "slow": slow_multiplier
    })
    queue_free()
