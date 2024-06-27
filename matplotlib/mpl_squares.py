import matplotlib.pyplot as plt

plt.style.use('seaborn-v0_8')
fig, ax = plt.subplots()
# input_values = [1, 2, 3, 4, 5]
# squares = [1, 4, 9, 16, 25]
# ax.plot(input_values, squares, linewidth=3)
x_values = range(1, 1001)
y_values = [x**2 for x in x_values]
ax.scatter(x_values, y_values, c=y_values, cmap=plt.cm.Blues, s=10)
ax.axis([0, 1100, 0, 1100000])
ax.ticklabel_format(style='plain', axis='both')

ax.set_title("Square Numbers", fontsize=24)
ax.set_xlabel("Value", fontsize=14)
ax.set_ylabel("Square of Value", fontsize=14)

ax.tick_params(labelsize=14)

plt.show()
# plt.savefig('', bbox_inches='tight')
