extends Node3D

@onready var house: Node3D = $House
@onready var camera: Camera3D = $Camera3D

var bounds_center := Vector3.ZERO
var bounds_size := 1.0

func _ready() -> void:
	var points: Array[Vector3] = []
	for node in house.find_children("*", "MeshInstance3D", true, false):
		var mesh := node as MeshInstance3D
		var aabb := mesh.get_aabb()
		for corner in [
			Vector3(aabb.position.x, aabb.position.y, aabb.position.z),
			Vector3(aabb.end.x, aabb.position.y, aabb.position.z),
			Vector3(aabb.position.x, aabb.end.y, aabb.position.z),
			Vector3(aabb.position.x, aabb.position.y, aabb.end.z),
			Vector3(aabb.end.x, aabb.end.y, aabb.position.z),
			Vector3(aabb.end.x, aabb.position.y, aabb.end.z),
			Vector3(aabb.position.x, aabb.end.y, aabb.end.z),
			Vector3(aabb.end.x, aabb.end.y, aabb.end.z)]:
			points.append(mesh.global_transform * corner)
	if points.is_empty():
		return
	var lo := points[0]
	var hi := points[0]
	for point in points:
		lo = lo.min(point)
		hi = hi.max(point)
	var center := (lo + hi) * 0.5
	var size := maxf(hi.x - lo.x, maxf(hi.y - lo.y, hi.z - lo.z))
	bounds_center = center
	bounds_size = size
	set_view(0)
	$CanvasLayer/Info.text = "ONLINE GLB\n%0.1f × %0.1f × %0.1f m\n%0.0f mesh nodes\n1 exterior · 2 foyer · 3 kitchen · 4 kitchen reverse" % [hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, points.size()]

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_1: set_view(0)
			KEY_2: set_view(1)
			KEY_3: set_view(2)
			KEY_4: set_view(3)

func set_view(index: int) -> void:
	var target := bounds_center
	match index:
		0:
			camera.position = bounds_center + Vector3(bounds_size * 1.2, bounds_size * 0.9, bounds_size * 1.1)
		1:
			camera.position = Vector3(1.9, 3.0, 0.0)
			target = Vector3(3.3, 2.4, -4.0)
		2:
			camera.position = Vector3(8.5, 3.0, -10.0)
			target = Vector3(10.5, 2.4, -14.5)
		3:
			camera.position = Vector3(11.0, 3.0, -16.0)
			target = Vector3(8.5, 2.4, -11.5)
	camera.look_at(target)
	camera.far = bounds_size * 5.0
