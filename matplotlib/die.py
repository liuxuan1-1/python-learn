from random import randint
import plotly.express as px


class Die:
    def __init__(self, num_sides=6):
        self.num_sides = num_sides

    def roll(self):
        return randint(1, self.num_sides)


die_1 = Die()
die_2 = Die()

results = []
for roll_num in range(10000):
    result = die_1.roll() + die_2.roll()
    results.append(result)

print(results)
frequencies = []
max_result = die_1.num_sides + die_2.num_sides
poss_results = range(2, max_result + 1)
for value in poss_results:
    frequency = results.count(value)
    frequencies.append(frequency)

print(frequencies)
labels = {'x': 'Result', 'y': 'Frequency of Result'}
fig = px.bar(x=poss_results, y=frequencies, title='Results of rolling one D6 100 times', labels=labels)
fig.update_layout(xaxis_dtick=1)
fig.show()
