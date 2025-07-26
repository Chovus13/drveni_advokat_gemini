# test_fix.py

# Uzimamo primer "slomljenog" teksta koji ste mi poslali
garbled_text = "OP[TINSKOM SUDU U BE^EJU, Do`a \\er|a br. 58, {est komada goblena}"

print(f"Originalni tekst: {garbled_text}")

# Naša mapa za "prevođenje" karaktera
# Proširićemo je na osnovu onoga što vidimo
correction_map = {
    '^': 'č',
    '[': 'š',
    ']': 'ž',
    '`': 'ć',
    '|': 'đ',
    '{': 'š', # Izgleda da imate više karaktera za isto slovo
    '}': 'ž'  # Kao i ovde
}

fixed_text = garbled_text
for bad_char, good_char in correction_map.items():
    fixed_text = fixed_text.replace(bad_char, good_char)

print(f"Ispravljen tekst: {fixed_text}")