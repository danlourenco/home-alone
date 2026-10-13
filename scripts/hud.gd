extends CanvasLayer

@onready var phase_label: Label = $MarginContainer/VBoxContainer/Phase
@onready var timer_label: Label = $MarginContainer/VBoxContainer/Timer
@onready var budget_label: Label = $MarginContainer/VBoxContainer/Budget
@onready var trap_label: Label = $MarginContainer/VBoxContainer/Trap
@onready var prompt_label: Label = $MarginContainer/VBoxContainer/Prompt

func set_phase(text: String):
	if phase_label:
		phase_label.text = text

func set_timer(text: String):
	if timer_label:
		timer_label.text = text

func set_budget(text: String):
	if budget_label:
		budget_label.text = text

func set_trap(text: String):
	if trap_label:
		trap_label.text = text

func set_prompt(text: String):
	if prompt_label:
		prompt_label.text = text
