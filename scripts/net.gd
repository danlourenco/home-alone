extends Node

const DEFAULT_PORT := 7000
var roles := {}

func _ready():
    multiplayer.peer_connected.connect(_on_peer_connected)
    multiplayer.peer_disconnected.connect(_on_peer_disconnected)

func host(port: int = DEFAULT_PORT):
    var peer := ENetMultiplayerPeer.new()
    peer.create_server(port, 3)
    multiplayer.multiplayer_peer = peer
    roles[multiplayer.get_unique_id()] = "kevin"
    _sync_spawn(multiplayer.get_unique_id(), "kevin")
    MatchManager.start_match()

func join(address: String = "127.0.0.1", port: int = DEFAULT_PORT):
    var peer := ENetMultiplayerPeer.new()
    peer.create_client(address, port)
    multiplayer.multiplayer_peer = peer

func _on_peer_connected(id: int):
    if not multiplayer.is_server():
        return
    var assigned_role = "spectator"
    if not roles.values().has("bandit"):
        assigned_role = "bandit"
    roles[id] = assigned_role
    if assigned_role != "spectator":
        rpc("receive_spawn", id, assigned_role)
    rpc_id(id, "sync_full_phase", int(MatchManager.phase), MatchManager.phase_time_left, MatchManager.trap_budget, MatchManager.selected_trap)

func _on_peer_disconnected(id: int):
    roles.erase(id)

@rpc("authority", "call_local", "reliable")
func receive_spawn(peer_id: int, role: String):
    _sync_spawn(peer_id, role)

func _sync_spawn(peer_id: int, role: String):
    MatchManager.spawn_player(peer_id, role)

@rpc("any_peer", "reliable")
func request_place_trap(socket_path: String, trap_name: String):
    if not multiplayer.is_server():
        return
    var sender = multiplayer.get_remote_sender_id()
    var role = roles.get(sender, "")
    if role != "kevin":
        return
    var socket = get_node_or_null(socket_path)
    if socket and not socket.has_trap() and MatchManager.can_afford(trap_name):
        MatchManager.spend_budget(trap_name)
        rpc("apply_trap", socket_path, trap_name)

@rpc("authority", "call_local", "reliable")
func apply_trap(socket_path: String, trap_name: String):
    var socket = get_node_or_null(socket_path)
    if socket and socket.has_method("place_trap"):
        socket.place_trap(trap_name)
