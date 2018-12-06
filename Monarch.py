#!/home/joshua/anaconda3/bin/python

from Pollinator import *
import numpy as np


class Monarch(Pollinator):
    """
    This class creates the Monarch.py butterfly object. The monarch is modeled as migrating north. It's movement is
    mainly north, unless it is seeking food or shelter. It will seek shelter when night approaches and food when it is
    hungry, unless it is sheltered. It enters on the edge of the field in a random position. It also has an element of
    randomness to it's movement, as wind currents can blow the insect off course.
    >>> f = CropField([[1, 2, 2, 1], [1, 2, 2, 1], [1, 2, 2, 1], [1, 2, 2, 1], [1, 2, 2, 1]])
    >>> b1 = Monarch.py(f)
    >>> b1.food_level = 100
    >>> b1.position = [1,3]
    >>> print(b1.food_level)
    100
    >>> b1.position
    [1, 3]
    >>> b1
    Monarch.py with 100.00% food at [1, 3]
    """
    food_unit = 0.0225
    __death_factor = 0.01
    __can_exit_north = True
    __exit_chance = 0.9
    __shelter_chance = 0.01

    def __init__(self, area: CropField):
        Pollinator.__init__(self, area)
        # This gives the starting position
        variable = np.random.choice([0, 1, 2, 3], p=[0.625, 0.125, 0.125, 0.125])
        if variable == 0:
            temp_position = [self.area_length - 1, np.random.randint(self.area_width)]
        elif variable == 1:
            temp_position = [np.random.randint(int(self.area_length/2), self.area_length-1), 0]
        elif variable == 2:
            temp_position = [np.random.randint(int(self.area_length/2), self.area_length-1), self.area_width-1]
        else:
            if self.shelter_indices:
                temp_position = list(self.shelter_indices[np.random.choice(len(self.shelter_indices))])
            else:
                temp_position = [self.area_length - 1, 0]
        self.position = temp_position
        self.moves = [temp_position]

    def morning_activity(self):
        '''
        For the first couple hours in the morning, monarchs will typically seek food.
        '''

        # If it's in shelter during the day light, there's a small chance it will just stay put, unless
        # it is super hungry
        if self.sheltered:
            # number of times it will move randomly
            times = np.random.randint(10)
            # Just a check to make sure it is actually in a tree area and marked as sheltered...
            if self.area.array[self.position[0]][self.position[1]] not in [3, 4]:
                self.sheltered = False
                self.random_move(times)
                # One turn consumes 25 seconds
                self.turns += times
            # if it's still sheltered but it's food level is low, or random chance kicks in, it will leave shelter
            elif self.food_level < 25 or np.random.choice([True, False], p=[0.1, 0.9]):
                self.sheltered = False
                self.random_move(times)
                self.seconds += times
            else:
                # just stay sheltered if those conditions fail
                # Consume half a unit of food
                self.decrement_food(self.__food_unit / 2)
                self.turns += 1
        else:
            self.seek_resource('food')

    def late_morning_activity(self):
        # If it's daylight, the priorities will be food if it's hungry and moving north otherwise.
        # It may randomly occasionally seek shelter if it happens to be near a tree.
        # If it's in shelter during the day light, there's a small chance it will just stay put, unless
        # it is super hungry
        # moves possible
        moves_possible = int(self.food_level // self.__food_unit)
        if self.sheltered:
            # number of times it moves randomly
            times = np.random.randint(10)
            # Just a check to make sure it is actually in a tree area and marked as sheltered...
            if self.area.array[self.position[0]][self.position[1]] not in [3, 4]:
                self.sheltered = False
                self.random_move(times)
                self.turns += times

            # If it's still sheltered, meaning its in a legal shelter site, then most likely it will move
            elif self.food_level < 25 or np.random.choice([True, False], p=[.9, .1]):
                self.sheltered = False
                self.random_move(times)
                self.turns += times

            # stay sheltered if those conditions fail
            else:
                self.decrement_food(self.__food_unit / 2)
                self.turns += 1
        else:
            # Above a 50% food level, we'll consider it
            if self.food_level >= 50.0:
                # Usually, it will try to move north

                move_die = np.random.choice(int(moves_possible // 2))

                for i in range(move_die):
                    direction_die = np.random.choice(['north', 'south', 'east', 'west'],
                                                     p=[0.925, 0.025, 0.025, 0.025])
                    random_chance = np.random.choice([0, 1], p=[.995, 0.005])
                    if random_chance:
                        self.random_move()
                    else:
                        self.simple_move(direction_die)

                    self.turns += 1

            # if it's a little hungry, it may seek food
            elif 25.0 <= self.food_level < 50.0:
                if np.random.choice([True, False], p=[0.001, 0.999]):
                    # slight chance of moving randomly instead
                    self.random_move()

                else:
                    # usually look for food
                    self.seek_resource('food')
                    return

            # now it's very hungry and will almost certainly seek food
            elif self.food_level < 25.0:
                if np.random.choice([True, False], p=[0.0001, 0.9999]):
                    self.random_move()

                # otherwise look for food
                else:
                    self.seek_resource('food')
                    return

    # For the afternoon, it will repeat the late-morning activity
    def afternoon_activity(self):
        self.late_morning_activity()
        return

    # As dusk approaches, it will try to look for food before sheltering for the night.
    # If it's already sheltered, we'll just have it stay sheltered.
    def late_afternoon_activity(self):
        # Number of times to randomly move
        times = np.random.randint(10)
        # If it's still sheltered at this point, break shelter
        if self.sheltered:
            self.sheltered = False
            self.random_move(times)
            self.decrement_food(self.__food_unit)
            self.turns += times
        else:
            # otherwise it's going to look for food to fill its belly before sleep
            self.seek_resource('food')
        return

    def night_time_activity(self):
        # During the evening, it will prioritize seeking shelter. It will stay in shelter through the night
        # once it locates it, so we'll remove the leave shelter component of the checks. There's no real
        # food to be had at night, so we'll just assume it battens down the hatches. If it's food falls too low
        # it may die. Such is the risk of life.

        # Number of times to randomly move
        times = np.random.randint(10)
        if self.sheltered:
            # At night it will batten down the hatches and stay sheltered
            # If for whatever reason it is marked as sheltered but isn't in a tree...
            if self.area.array[self.position[0]][self.position[1]] not in [3, 4]:
                self.sheltered = False
                self.random_move(times)
                self.turns += times
            else:
                # if it gets here, it's sheltered and in a tree, so just decrement half a food unit
                # and move aling without taking further action
                self.decrement_food(self.__food_unit / 2)
                return
        # This is the case that it is alive and near shelter. At this time it will take shelter
        elif self.area.array[self.position[0]][self.position[1]] in [3, 4]:
            self.sheltered = True
            self.decrement_food(self.__food_unit / 2)

        else:
            # otherwise it's going to look for shelter
            self.seek_resource('shelter')
        return