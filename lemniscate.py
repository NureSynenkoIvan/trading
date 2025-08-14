import math
import matplotlib.pyplot as plt

sqrt2 = math.sqrt(2)

def lemniscate(x):
    return math.sqrt(-2 * (x**2) + math.sqrt(8 * x**2 + 1) - 1) / sqrt2

x_values = []
y_values = []

x = -1.0
while x < 1.0:
    x_values.append(x)
    y_values.append(lemniscate(x))
    x += 0.1

while x > -1.0:
    x_values.append(x)
    y_values.append(lemniscate(x))
    x -= 0.1

# Побудова графіка
plt.plot(x_values, y_values, marker='o', linestyle='-')
plt.xlabel("x")
plt.ylabel("y")
plt.title("Графік функції lemniscate(x)")
plt.grid()
plt.show()