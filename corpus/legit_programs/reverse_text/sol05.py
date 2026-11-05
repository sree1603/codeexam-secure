text = input()

characters = []

for character in text:
    characters.insert(0, character)

print("".join(characters))
