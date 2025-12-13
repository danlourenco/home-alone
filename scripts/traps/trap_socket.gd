extends Node3D

@export var socket_name: String = "Socket"
var placed_trap: Node3D

func _ready():
    add_to_group("trap_sockets")

func has_trap() -> bool:
    return placed_trap != null

func clear_trap():
    if placed_trap:
        placed_trap.queue_free()
        placed_trap = null

func place_trap(trap_name: String):
    clear_trap()
    var scene: PackedScene = MatchManager.get_trap_scene(trap_name)
    if scene:
        placed_trap = scene.instantiate()
        add_child(placed_trap)

func get_prompt() -> String:
    if has_trap():
        return "%s: armed" % socket_name
    return "%s: empty" % socket_name
