text = input()

characters = list(text)
result = ""

while characters:
    result += characters.pop()

print(result)
