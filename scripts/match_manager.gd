extends Node

enum Phase { PREP, BREACH, END }

const PREP_TIME := 45.0
const BREACH_TIME := 180.0
const END_TIME := 10.0

var phase: Phase = Phase.PREP
var phase_time_left: float = PREP_TIME
var trap_budget: int = 100
var selected_trap: String = "Micro Machines"

var trap_scenes := {
    "Micro Machines": preload("res://scenes/traps/MicroMachines.tscn"),
    "Blowtorch Door": preload("res://scenes/traps/BlowtorchDoor.tscn"),
    "Paint Can": preload("res://scenes/traps/PaintCan.tscn"),
    "Icy Steps": preload("res://scenes/traps/IcySteps.tscn")
}

const TRAP_ORDER := ["Micro Machines", "Blowtorch Door", "Paint Can", "Icy Steps"]

var trap_costs := {
    "Micro Machines": 15,
    "Blowtorch Door": 25,
    "Paint Can": 30,
    "Icy Steps": 20
}

var hud: CanvasLayer
var time_sync_accum := 0.0

func _ready():
    if not hud:
        hud = get_tree().current_scene.get_node_or_null("HUD")
    _update_hud()
    if multiplayer.is_server():
        start_match()

func _process(delta):
    if multiplayer.is_server():
        _tick_phase(delta)
        time_sync_accum += delta
        if time_sync_accum > 0.5:
            rpc("sync_time", phase_time_left)
            time_sync_accum = 0.0
    _update_timer_label()

func start_match():
    trap_budget = 100
    selected_trap = "Micro Machines"
    _clear_traps()
    _set_phase(Phase.PREP, PREP_TIME)

func _tick_phase(delta: float):
    phase_time_left -= delta
    if phase_time_left > 0:
        return
    if phase == Phase.PREP:
        _set_phase(Phase.BREACH, BREACH_TIME)
    elif phase == Phase.BREACH:
        _set_phase(Phase.END, END_TIME)
    elif phase == Phase.END:
        start_match()

func _set_phase(new_phase: Phase, time_left: float):
    phase = new_phase
    phase_time_left = time_left
    rpc("sync_phase", phase, phase_time_left)
    _update_hud()

@rpc("authority", "call_local", "reliable")
func sync_phase(new_phase: int, time_left: float):
    phase = Phase.values()[new_phase]
    phase_time_left = time_left
    _update_hud()

func _update_timer_label():
    if not hud:
        return
    var minutes = int(phase_time_left) / 60
    var seconds = int(phase_time_left) % 60
    hud.set_timer("%02d:%02d" % [minutes, seconds])

@rpc("authority", "call_local", "unreliable")
func sync_time(time_left: float):
    phase_time_left = time_left
    _update_timer_label()

func _update_hud():
    if not hud:
        return
    var phase_name = ["PREP", "BREACH", "END"][int(phase)]
    hud.set_phase("Phase: %s" % phase_name)
    hud.set_budget("Budget: %d" % trap_budget)
    hud.set_trap("Selected Trap: %s" % selected_trap)

func get_trap_scene(trap_name: String) -> PackedScene:
    return trap_scenes.get(trap_name, null)

func get_selected_trap() -> String:
    return selected_trap

@rpc("authority", "call_local", "reliable")
func sync_full_phase(new_phase: int, time_left: float, budget: int, selection: String):
    phase = Phase.values()[new_phase]
    phase_time_left = time_left
    trap_budget = budget
    selected_trap = selection
    _update_hud()

func set_selected_trap_by_index(idx: int):
    if idx >= 0 and idx < TRAP_ORDER.size():
        selected_trap = TRAP_ORDER[idx]
        rpc("sync_selection", selected_trap)
        _update_hud()

@rpc("any_peer", "call_local", "reliable")
func sync_selection(name: String):
    selected_trap = name
    _update_hud()

func can_afford(name: String) -> bool:
    return trap_budget >= trap_costs.get(name, 999)

func spend_budget(name: String):
    trap_budget -= trap_costs.get(name, 0)
    rpc("sync_budget", trap_budget)
    _update_hud()

@rpc("authority", "call_local", "reliable")
func sync_budget(amount: int):
    trap_budget = amount
    _update_hud()

func set_socket_prompt(text: String):
    if hud:
        hud.set_prompt(text)

func spawn_player(peer_id: int, role: String):
    var scene: PackedScene = null
    if role == "kevin":
        scene = preload("res://scenes/players/Kevin.tscn")
    elif role == "bandit":
        scene = preload("res://scenes/players/Bandit.tscn")
    if scene:
        var instance = scene.instantiate()
        instance.name = "%s_%d" % [role.capitalize(), peer_id]
        instance.multiplayer_authority = peer_id
        var spawns = get_tree().current_scene.get_node_or_null("Spawns")
        if spawns:
            var spawn = spawns.get_node_or_null("%sSpawn" % role.capitalize())
            if spawn:
                instance.global_transform = spawn.global_transform
        get_tree().current_scene.add_child(instance, true)

func _clear_traps():
    for socket in get_tree().get_nodes_in_group("trap_sockets"):
        socket.clear_trap()
