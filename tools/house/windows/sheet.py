from PIL import Image, ImageDraw
UP = "/Users/dlo/Dev/home-alone/sfm-work/rooms/girls/all/images/f_00041.jpg"
GR = "/Users/dlo/Dev/home-alone/sfm-work/ground/overhead_994.jpg"
T = [  # label, image, crop box
 ("UP parents side_bank (ovh)", UP, (800, 50, 1130, 140)), ("UP parents front_twin 240s", "f2_240.jpg", (850, 80, 1750, 900)),
 ("UP parents front_twin 182s", "f2_182.jpg", (200, 150, 1150, 900)), ("UP parents_bath rear 209s", "f2_209.jpg", (580, 180, 1340, 1000)),
 ("UP kevin front x2 356s", "f2_356.jpg", (720, 30, 1910, 700)), ("UP kevin front (ovh)", UP, (1240, 255, 1320, 480)),
 ("UP hall_bath front (ovh)", UP, (1250, 480, 1330, 690)), ("UP girls_a rear (ovh)", UP, (620, 330, 700, 470)),
 ("UP girls_b rear x2 (ovh)", UP, (590, 700, 680, 1010)),
 ("GR den side_twin 556s", "f1_556.jpg", (500, 100, 1920, 900)), ("GR den side (ovh)", GR, (225, 440, 330, 920)),
 ("GR den front_wide 586s", "f1_586.jpg", (500, 0, 1920, 1000)), ("GR den front (ovh)", GR, (225, 870, 545, 935)),
 ("GR living rear x2 458s", "f1_458.jpg", (590, 240, 1510, 760)), ("GR living front French x2 438s", "f1_438.jpg", (140, 180, 1400, 800)),
 ("GR living front (ovh)", GR, (480, 920, 820, 975)), ("GR dining front French (ovh)", GR, (1040, 920, 1360, 975)),
 ("GR dining front French 214s", "f1_214.jpg", (230, 30, 560, 920)),
 ("GR kitchen back_door+sink (ovh)", GR, (1220, 50, 1480, 160)), ("GR kitchen back_door+sink 1096s", "f1_1096full.jpg", (150, 250, 1250, 900)),
 ("GR kitchen side_rear+seat 945s", "f1_945full.jpg", (1050, 120, 1920, 750)), ("GR kitchen side_front 896s", "f1_896full.jpg", (0, 0, 1300, 800)),
 ("GR kitchen side (ovh)", GR, (1420, 60, 1540, 470)), ("GR kitchen breakfast_rear (ovh)", GR, (1090, 240, 1250, 320)),
 ("GR kitchen side_upper exterior (ovh)", GR, (1170, 50, 1250, 260)),
]
W, H = 360, 230
sheet = Image.new("RGB", (W * 5, (H + 18) * ((len(T) + 4) // 5)), "black")
d = ImageDraw.Draw(sheet)
for i, (lab, p, b) in enumerate(T):
    im = Image.open(p).convert("RGB").crop(b); im.thumbnail((W, H))
    x, y = (i % 5) * W, (i // 5) * (H + 18)
    sheet.paste(im, (x + (W - im.width) // 2, y + 18)); d.text((x + 4, y + 3), lab, fill=(255, 255, 0))
sheet.save("windows-contact.png"); print(sheet.size)
