import numpy as np
import math
import time
import os
import signal
import sys
from threading import Timer
import multiprocessing


class Area:
    """
    A generic area, consisting of a length and width, 1 unit of length = 1 unit of
    width = 15 meters. This will form the basis of the CropField class. It takes a two-dimensional array
    as an input and converts it into a numpy array, then checks that it is a true 2D array (a list of lists,
    with all sublists being the same length)
    """

    def __init__(self, array):
        # convert input array to numpy array
        self.array = np.array(array)
        self.shape = self.array.shape
        self.row_len = self.shape[0]
        # checks that it is a 2D array and not a simple list
        assert type(self.array[0]) is not int, "Area must be a 2-dimensional list, e.g., [[1,1],[1,1]]."
        # this checks that every sublist is the same length. Numpy's shape returns a tuple with the second element
        # empty if the sublists have different lengths. So this simply gives a more meaningful error
        try:
            self.col_len = self.shape[1]
        except (ValueError, IndexError):
            print("Subarrays must be the same length")
            sys.exit(1)

    def __str__(self) -> str:
        """
        Prints the dimensions of the area. Each extra row and column adds 15 meetrs to the dimensions
        :return: string for printing
        """
        return '{} m x {} m area'.format(
            self.row_len * 15, self.col_len * 15)

    def __repr__(self):
        """
        Basically the same as above, but adds the "Area" class designation
        :return: string for printing
        """
        return "Area('{} m x {} m')".format(
            self.row_len * 15, self.col_len * 15)


class CropField(Area):
    """
    This is a versioun of the Area class that takes an input array with all elements being equal to 1, 2, or 3.
    Where 1 is a crop, 2 food, and 3 shelter. It can print out a simple graphic interpretation of this array
    (with '=' being crop, 'o' being a food source, and '*' being shelter (trees))
    TODO: Create a better graphical representation
    """

    def __init__(self, array):
        # Initializes the object as an Area class to check that it is truly 2D
        Area.__init__(self, array)
        values = [1, 2, 3]
        if False in np.isin(self.array, values):
            raise ValueError("Values of CropField must be either 1 (crop), 2 (food), or 3 (shelter)")
        ix_food = np.isin(self.array, 2)
        self.food_indices = []
        if True in ix_food:
            self.food_indices = list(zip(np.where(ix_food)[0], np.where(ix_food)[1]))
        ix_shelter = np.isin(self.array, 3)
        self.shelter_indices = []
        if True in ix_shelter:
            self.shelter_indices = list(zip(np.where(ix_shelter)[0], np.where(ix_shelter)[1]))

    def __to_string(self):
        string_version = ''
        for row in range(self.row_len):
            for column in range(self.col_len):
                if self.array[row][column] == 1:
                    string_version += '='
                elif self.array[row][column] == 2:
                    string_version += 'o'
                elif self.array[row][column] == 3:
                    string_version += '*'
                else:
                    print("values must be either 1 (crop), 2 (food), or 3 (shelter)")
            if row != self.row_len:
                string_version += '\n'
        return string_version

    def __str__(self) -> str:
        return self.__to_string()

    def __repr__(self) -> str:
        return self.__to_string()

    def get_crop_amt(self):
        return (self.array == 1).sum()

    def get_food_amt(self):
        return (self.array == 2).sum()

    def get_shelter_amt(self):
        return (self.array == 3).sum()

    def raw(self):
        string_version = ''
        for row in range(self.row_len):
            for column in range(self.col_len):
                string_version += str(self.array[row][column])
                if column != self.col_len - 1:
                    string_version += " "
            if row != self.row_len:
                string_version += '\n'
        print(string_version)

    @classmethod
    def random_field(cls, length, width, percent_crops=100, percent_food=0, percent_shelter=0):
        # creates a random field given the dimensions. Picks placement of food and shelter randomly
        if percent_crops + percent_food + percent_shelter != 100:
            raise ValueError("The percentages do not add up to 100")
        area = length * width
        # find the number of squares for each type of cell
        number_crop_cells = math.ceil(percent_crops / 100 * area)
        number_food_cells = math.ceil(percent_food / 100 * area)
        number_shelter_cells = math.floor(percent_shelter / 100 * area)
        # if the calculations produced more or less of the squares needed, this should clean it up.
        # there shouldn't be more than three cells difference because of how I rounded it, so this shouldn't
        # affect the final result much
        distro = area - (number_crop_cells + number_food_cells + number_shelter_cells)
        # I'll prioritize adding shelter cells if they elected to have them, or else I'll add food cells
        # I feel like most farmers would prioritize wind breaks over feeding butterflies
        while distro > 0:
            if number_shelter_cells > 0:
                number_shelter_cells += 1
            else:
                number_food_cells += 1
            distro = area - (number_crop_cells + number_food_cells + number_shelter_cells)
        # If there are any food cells, remove those first, then shelter cells
        while distro < 0:
            if number_food_cells > 0:
                number_food_cells -= 1
            else:
                number_shelter_cells -= 1
            distro = area - (number_crop_cells + number_food_cells + number_shelter_cells)
        try:
            distro == 0
        except ValueError:
            print('something went wrong in the cell calculations')
            sys.exit(1)
        random_f = np.full((length, width), 1, dtype=int).tolist()
        while number_shelter_cells + number_food_cells > 0:
            if number_shelter_cells > 0:
                temp_length = np.random.randint(0, length - 1)
                temp_width = np.random.randint(0, width - 1)
                if random_f[temp_length][temp_width] == 1:
                    random_f[temp_length][temp_width] = 3
                    number_shelter_cells -= 1
            if number_food_cells > 0:
                temp_length = np.random.randint(0, length - 1)
                temp_width = np.random.randint(0, width - 1)
                if random_f[temp_length][temp_width] == 1:
                    random_f[temp_length][temp_width] = 2
                    number_food_cells -= 1
        return cls(random_f)


class Pollinator:
    """
    Generic Pollinator class which the others will be based on. All animals are tied to an area, so there must be an
    area first to have an animal
    """

    __food_unit = 0
    __death_factor = 0

    def __init__(self, area: Area):
        # Pollinators start out alive with a random amount of food
        self.food_level = float(np.random.randint(0, 101))
        self.status = "alive"
        self.area_length = area.shape[0]
        self.area_width = area.shape[1]
        self.area = area
        self.position = [0, 0]

    def __str__(self):
        return '{} with {:.2f}% food at {}'.format(type(self).__name__, self.food_level, self.position)

    def __repr__(self):
        return '{} with {:.2f}% food at {}'.format(type(self).__name__, self.food_level, self.position)

    def kill_it(self):
        self.status = 'dead'
        return self

    def check_for_death(self):
        # Based on how much food it currently has, the Monarch's chances to die randomly change.
        roll_die = np.random.random_sample()
        if self.food_level > 90 and roll_die < self.__class__.__death_factor/1000:
            self.kill_it()
            return self
        elif 50.0 < self.food_level <= 90 and roll_die < self.__class__.__death_factor/100:
            self.kill_it()
            return self
        elif 25.0 < self.food_level <= 50.0 and roll_die <= self.__class__.__death_factor:
            self.kill_it()
            return self
        elif 0.01 <= self.food_level <= 25.0 and roll_die < self.__class__.__death_factor * 50:
            self.kill_it()
            return self
        elif self.food_level < 0.01 and roll_die < self.__class__.__death_factor * 99:
            self.kill_it()
            return self
        else:
            return self

    def decrement_food(self, amount):
        if self.food_level >= amount:
            self.food_level -= amount
        else:
            self.food_level = 0
        return self

    def random_move(self, number: int = 1):
        # The pollinator moves randomly
        if self.__class__.can_exit and self.position[0] == 0:
            self.status = np.random.choice(['exit', 'alive'], p=[.90, .1])
        for i in range(number):
            coord = np.random.choice((0, 1))
            direction = np.random.choice((-1, 1))
            if coord == 0:
                # Move north-south
                if self.area_length - 1 > self.position[0] > 0:
                    self.position[coord] += direction
                    self.decrement_food(self.__food_unit)
                else:
                    self.check_for_death()
            else:
                # Move east-west
                if self.area_width - 1 > self.position[1] > 0:
                    self.position[1] += direction
                    self.decrement_food(self.__food_unit)
                else:
                    self.check_for_death()
        return self

    def simple_move(self, direction: str = 'north'):
        """
        This method simply moves the monarch one unit in one direction. It's specific to the butterfly because
        it will try to leave if it is on the northernmost border. Other pollinators might not behave this way
        :param direction: A string giving the ordinal direction
        :return: simple returns the updated butterfly
        >>> testfield = CropField.random_field(100,100,90,5,5)
        >>> b1 = Monarch(testfield)
        >>> b1.simple_move("worst")
        Traceback (most recent call last):
          File "C:\Program Files\JetBrains\PyCharm 2018.2.3\helpers\pycharm\docrunner.py", line 140, in __run
            compileflags, 1), test.globs)
          File "<doctest simple_move[2]>", line 1, in <module>
            b1.simple_move("worst")
          File "C:/Users/Joshua/PycharmProjects/monarch_simulation/Butterflies.py", line 205, in simple_move
            assert (direction == 'north' or direction == 'south' or direction == 'east' or direction == 'west')
        AssertionError
        >>> b1.position = [50,50]
        >>> b1.simple_move('north')
        >>> print(b1.position)
        [49, 50]
        >>> b1.position = [100,50]
        >>> b1.food_level = 20
        >>> b1.simple_move("North")
        Monarch with 20.00% food at [100, 50]
        >>> b1.status
        'exit'
        """
        # Ensure a valid ordinal direction was passed into the function
        direction = direction.lower()
        assert (direction == 'north' or direction == 'south' or direction == 'east' or direction == 'west')
        # Different pollinators may have different behavior. Monarchs will leave the map, so we want to put some special
        # checks on them. A pollinator that can't leave the area will have different behavior.
        if self.__class__.can_exit and self.position[0] == 0:
            self.status = np.random.choice(['exit', 'alive'], p=[.90, .1])
            if self.position[0] < 0 or self.position[0] >= self.area_length or \
                    self.position[1] < 0 or self.position[1] >= self.area_width:
                self.status = 'exit'
                return self
            # if the monarch is on the top row, it will try to leave
            if self.position[0] == 0:
                self.status = np.random.choice(['exit', 'alive'], p=[0.9, 0.1])
                if self.status == 'alive':
                    self.random_move()
                    self.check_for_death()
                    return self
                else:
                    return self
        else:
            # if the pollinator is on the border, move randomly
            if self.position[0] == 0 or self.position[0] == self.area_length - 1 or \
                    self.position[1] == 0 or self.position[1] == self.area_width - 1:
                self.random_move()

            # Otherwise it will make a basic moves
            elif direction == 'north':
                self.position[0] -= 1
                self.decrement_food(self.__food_unit)
                self.check_for_death()
            elif direction == 'south':
                self.position[0] += 1
                self.decrement_food(self.__food_unit)
                self.check_for_death()
            elif direction == 'east':
                self.position[1] += 1
                self.decrement_food(self.__food_unit)
                self.check_for_death()
            elif direction == 'west':
                self.position[1] -= 1
                self.decrement_food(self.__food_unit)
                self.check_for_death()
            else:
                raise ValueError("Direction not recognized")

class Monarch(Pollinator):
    """
    This class creates the Monarch butterfly object. The monarch is modeled as migrating north. It's movement is
    mainly north, unless it is seeking food or shelter. It will seek shelter when night approaches and food when it is
    hungry, unless it is sheltered. It enters on the edge of the field in a random position. It also has an element of
    randomness to it's movement, as wind currents can blow the insect off course.
    >>> f = CropField([[1, 2, 2, 1], [1, 2, 2, 1], [1, 2, 2, 1], [1, 2, 2, 1], [1, 2, 2, 1]])
    >>> b1 = Monarch(f)
    >>> b1.food_level = 100
    >>> b1.position = [1,3]
    >>> print(b1.food_level)
    100
    >>> b1.position
    [1, 3]
    >>> b1
    Monarch with 100% food at [1, 3]
    """

    __food_unit = 0.0225
    __death_factor = 0.01

    def __init__(self, area: CropField):
        Pollinator.__init__(self, area)
        self.sheltered = True
        self.food_indices = area.food_indices
        self.shelter_indices = area.shelter_indices
        # This gives the starting position
        variable = np.random.choice([0, 0, 0, 0, 0, 1, 2, 3])
        if variable == 0:
            self.position = [self.area_length - 1, np.random.randint(self.area_width)]
        elif variable == 1:
            self.position = [np.random.randint(int(self.area_length / 2)), 0]
        elif variable == 2:
            self.position = [np.random.randint(int(self.area_length / 2)), self.area_width - 1]
        else:
            if self.shelter_indices:
                self.position = list(self.shelter_indices[np.random.choice(len(self.shelter_indices))])
            else:
                self.position = [0, self.area_length-1]

    def check_for_death(self):
        # Based on how much food it currently has, the Monarch's chances to die randomly change.
        roll_die = np.random.random_sample()
        if self.food_level > 90:
            if roll_die < self.__death_factor/1000:
                self.kill_it()
                return self
            else:
                return self
        elif 50.0 < self.food_level <= 90:
            if roll_die < self.__death_factor/100:
                self.kill_it()
                return self
            else:
                return self
        elif 25.0 < self.food_level <= 50.0:
            if roll_die <= self.__death_factor:
                self.kill_it()
                return self
            else:
                return self
        elif 0.01 <= self.food_level <= 25.0:
            if roll_die < self.__death_factor * 50:
                self.kill_it()
                return self
            else:
                return self
        elif self.food_level < 0.01:
            if roll_die < self.__death_factor * 99:
                self.kill_it()
                return self
        else:
            self.kill_it()  # This catches any zombie butterflies
            return self

    def decrement_food(self, amount):
        if self.food_level >= amount:
            self.food_level -= amount
        else:
            self.food_level = 0
        return self

    def random_move(self, number: int = 1):
        # The pollinator moves randomly
        for i in range(number):
            coord = np.random.choice((0, 1))
            direction = np.random.choice((-1, 1))
            if coord == 0:
                # Move north-south
                if self.area_length - 1 > self.position[0] > 0:
                    self.position[coord] += direction
                    self.decrement_food(self.__food_unit)
                else:
                    self.check_for_death()
            else:
                # Move east-west
                if self.area_width - 1 > self.position[1] > 0:
                    self.position[1] += direction
                    self.decrement_food(self.__food_unit)
                else:
                    self.check_for_death()
        return self

    def simple_move(self, direction: str = 'north'):
        """
        This method simply moves the monarch one unit in one direction. It's specific to the butterfly because
        it will try to leave if it is on the northernmost border. Other pollinators might not behave this way
        :param direction: A string giving the ordinal direction
        :return: simple returns the updated butterfly
        >>> testfield = CropField.random_field(100,100,90,5,5)
        >>> b1 = Monarch(testfield)
        >>> b1.simple_move("worst")
        Traceback (most recent call last):
          File "C:\Program Files\JetBrains\PyCharm 2018.2.3\helpers\pycharm\docrunner.py", line 140, in __run
            compileflags, 1), test.globs)
          File "<doctest simple_move[2]>", line 1, in <module>
            b1.simple_move("worst")
          File "C:/Users/Joshua/PycharmProjects/monarch_simulation/Butterflies.py", line 205, in simple_move
            assert (direction == 'north' or direction == 'south' or direction == 'east' or direction == 'west')
        AssertionError
        >>> b1.position = [50,50]
        >>> b1.simple_move('north')
        >>> print(b1.position)
        [49, 50]
        >>> b1.position = [100,50]
        >>> b1.food_level = 20
        >>> b1.simple_move("North")
        Monarch with 20.00% food at [100, 50]
        >>> b1.status
        'exit'
        """
        # Ensure a valid ordinal direction was passed into the function
        direction = direction.lower()
        assert (direction == 'north' or direction == 'south' or direction == 'east' or direction == 'west')
        # Different pollinators may have different behavior. Monarchs will leave the map, so we want to put some special
        # checks on them. A pollinator that can't leave the area will have different behavior.
        if self.__class__ == Monarch:
            # if the bug is off the map, we'll mark it as having left
            if self.position[0] < 0 or self.position[0] >= self.area_length or \
                    self.position[1] < 0 or self.position[1] >= self.area_width:
                self.status = 'exit'
                return self
            # if the monarch is on the top row, it will try to leave
            if self.position[0] == 0:
                self.status = np.random.choice(['exit', 'alive'], p=[0.9, 0.1])
                if self.status == 'alive':
                    self.random_move()
                    self.check_for_death()
                    return self
                else:
                    return self
        # if it's on the border, move randomly
        if self.position[0] == 0 or self.position[0] == self.area_length - 1 or \
                self.position[1] == 0 or self.position[1] == self.area_width - 1:
            self.random_move()

        # These will be the basic moves
        if direction == 'north':
            self.position[0] -= 1
            self.decrement_food(self.__food_unit)
            self.check_for_death()
        elif direction == 'south':
            self.position[0] += 1
            self.decrement_food(self.__food_unit)
            self.check_for_death()
        elif direction == 'east':
            self.position[1] += 1
            self.decrement_food(self.__food_unit)
            self.check_for_death()
        elif direction == 'west':
            self.position[1] -= 1
            self.decrement_food(self.__food_unit)
            self.check_for_death()
        else:
            raise ValueError("Direction not recognized")

    def move_one_day(self, seconds: int=0, hours: int=4, days: int=0):
        """
        This is a long bunch of loops and if statements that basically amount to: move north unless you are hungry,
        in which case move toward food. Every once in awhile move toward shelter (rain simulation)
        One day is 86400 seconds. The day begins at 4 am, which should be light everywhere with in
        the monarch's range in the spring/summer when it is moving north. Because we are assuming that the
        butterfly covers this amount of distance in a day, One unit of movement thus represents about 26 seconds.
        This accounts for all the random fluttering and stopping that a butterfly does as it traverses 15 meters.
        Therefore, the counter will increase 25 seconds per loop (to simplify the math). Night wil be assumed 
        to start at 9pm, giving it 17 hours of day and 7 hours of night. During the night it will prioritize 
        seeking shelter. To allow for multiple butterflies, Seconds and hours will be an input into this 
        method.
        TODO: More than one butterfly will attempt to group together for shared warmth.
        :param hours: current number of seconds
        :param seconds: current hours
        :return: the Monarch object, appropriately manipulated
        """
        # seconds = 0
        # hour = 4 # keeping these here for reference for now
        flag = False
        while self.status == 'alive':
            # Check on the number of possible moves
            moves_possible = int(self.food_level // self.__food_unit)

            # this is a check to ensure we are modeling the day from 4am to 4 am.
            if flag:
                return self, days, seconds, hours
            increment_day(seconds, hours)

            # For the first couple hours in the morning, monarchs will typically seek food.
            if 4 <= hours < 6:
                # If it's in shelter during the day light, there's a small chance it will just stay put, unless
                # it is super hungry
                if self.sheltered:
                    # First decrement his food level by half the active amount
                    self.decrement_food(self.__food_unit/2)
                    # Just a check to make sure it is actually in a tree area and marked as sheltered...
                    if self.area.array[self.position[0]][self.position[1]] != 3:
                        self.sheltered = False
                        self.random_move()
                        # One turn consumes 25 seconds
                        seconds += 25
                    if self.sheltered and (self.food_level < 25 or np.random.choice([True, False], p=[.99, .01])):
                        self.sheltered = False
                        self.random_move()
                        # One turn consumes 25 seconds
                        seconds += 25
                    else:
                        pass
                        # just stay sheltered if those conditions fail
                        # Consume half a unit of food
                        self.decrement_food(self.__food_unit/2)
                        # One turn consumes 25 seconds
                        seconds += 25
                else:
                    self, turns = self.seek_resource('food')
                    # One turn consumes 25 seconds
                    seconds += (25 * turns)

                # make sure it's not a zombie butterfly
                self.check_for_death()
                if self.status == 'dead':
                    break

            # If it's daylight, the priorities will be food if it's hungry and moving north otherwise.
            # It may randomly occasionally seek shelter if it happens to be near a tree.
            elif 6 <= hours < 19:
                # If it's in shelter during the day light, there's a small chance it will just stay put, unless
                # it is super hungry
                if self.sheltered:
                    # Just a check to make sure it is actually in a tree area and marked as sheltered...
                    if self.area.array[self.position[0]][self.position[1]] != 3:
                        self.sheltered = False
                        self.random_move()
                        # One turn consumes 25 seconds
                        seconds += 25

                    # If it's still sheltered, meaning its in a legal shelter site, then most likely it will move
                    if self.sheltered and (self.food_level < 25 or np.random.choice([True, False], p=[0.99, 0.91])):
                        self.sheltered = False
                        self.random_move()
                        # One turn consumes 25 seconds
                        seconds += 25

                    else:
                        pass
                        self.decrement_food(self.__food_unit/2)
                        seconds += 25
                else:
                    # Above a 50% food level, we'll consider it full
                    if self.food_level >= 50.0:
                        # Usually, it will try to move north
                        direction_die = np.random.choice(['north', 'south', 'east', 'west'],
                                                         p=[.925, .025, .025, 0.025])
                        move_die = np.random.choice(int(moves_possible//2))

                        for i in range(move_die):
                            random_chance = np.random.choice([0, 1], p=[.995, 0.005])
                            if random_chance:
                                self.random_move()
                            else:
                                self.simple_move(direction_die)

                            # Each move takse 25 seconds
                            seconds += 25

                    # if it's a little hungry, it may seek food
                    elif 25.0 <= self.food_level < 50.0:
                        if np.random.choice([True, False], p=[0.001, 0.999]):
                            # slight chance of moving randomly instead
                            self.random_move()

                        else:
                            # usually look for food
                            self, turns = self.seek_resource('food')

                        if self.status == 'dead':
                            break

                        # Each move takse 25 seconds
                        seconds += (25 * turns)

                    # now it's very hungry and will almost certainly seek food
                    elif self.food_level < 25.0:
                        if np.random.choice([True, False], p=[0.0001, 0.9999]):
                            self.random_move()
                        # otherwise look for food
                        else:
                            self, turns = self.seek_resource('food')
                            if self.status == 'dead':
                                break
                        # check for death
                        if self.status == 'dead':
                            break

                        # Each move takse 25 seconds
                        seconds += (25 * turns)

                    # make sure it's not a zombie butterfly
                    self.check_for_death()
                    if self.status == 'dead':
                        break

            # As dusk approaches, it will try to look for food before sheltering for the night.
            # If it's already sheltered, we'll just have it stay sheltered.
            elif 19 <= hours < 21:
                if self.sheltered and self.status == 'alive':
                    # At night it will batten down the hatches and stay sheltered
                    # If for whatever reason it is marked as sheltered but isn't in a tree...
                    if self.area.array[self.position[0]][self.position[1]] != 3:
                        self.sheltered = False
                        self.random_move()
                        self.decrement_food(self.__food_unit)
                        # Each move takse 25 seconds
                        seconds += (25 * turns)
                    if self.status == 'dead':
                        break
                else:
                    # otherwise it's going to look for shelter
                    self, turns = self.seek_resource('shelter')
                    seconds += (25 * turns)

                # make sure it's not a zombie butterfly
                self.check_for_death()
                if self.status == 'dead':
                    break

            # During the evening, it will prioritize seeking shelter. It will stay in shelter through the night
            # once it locates it, so we'll remove the leave shelter component of the checks. There's no real 
            # food to be had at night, so we'll just assume it battens down the hatches. If it's food falls too low
            # it may die. Such is the risk of life.
            elif 21 <= hours < 24 or 0 <= hours < 4:
                # Quick check to make sure it is still alive before we do all this work
                if self.sheltered and self.status == 'alive':
                    # At night it will batten down the hatches and stay sheltered
                    # If for whatever reason it is marked as sheltered but isn't in a tree...
                    if self.area.array[self.position[0]][self.position[1]] != 3:
                        self.sheltered = False
                        self.random_move()
                        seconds += 25

                    if self.status == 'dead':
                        break
                else:
                    # otherwise it's going to look for shelter
                    self, turns = self.seek_resource('shelter')
                    seconds += (25 * turns)

                # make sure it's not a zombie butterfly
                self.check_for_death()
                if self.status == 'dead':
                    break

            else:
                raise ValueError("hours out of range during move")

            # now that it has moved, if it's near shelter, there's a small chance it may take shelter
            if self.area.array[self.position[0]][self.position[1]] == 3:
                if np.random.choice([True, False], p=[0.01, 0.99]):
                    self.sheltered = True

            # if it's near food, it will most likely try to eat
            if self.area.array[self.position[0]][self.position[1]] == 2:
                if np.random.choice([True, False], p=[0.95, 0.05]):
                    self.food_level = 100

        return self, seconds, hours

    def seek_resource(self, resource):
        # Let's make sure no zombie butterflies are looking for our resources
        if self.status == 'dead':
            return self

        if resource == 'shelter':
            if not self.shelter_indices:
                # There's no shelter, so it just wanders :(
                self.random_move()
                return self
            else:
                if tuple(self.position) in self.shelter_indices:
                    nearest = tuple(self.position)
                else:
                    nearest = min(self.shelter_indices, key=lambda x: distance(x, self.position))

        elif resource == 'food':
            if not self.food_indices:
                # There's no food, so it just wanders :(
                self.random_move()
                return self
            else:
                if tuple(self.position) in self.food_indices:
                    nearest = tuple(self.position)
                else:
                    nearest = min(self.food_indices, key=lambda x: distance(x, self.position))

        else:
            raise ValueError('Unknown resource')

        # There's a random chance it can't reach the resource, otherwise it does
        # and spends the appropriate amount of energy to get there

        if np.random.choice([1, 0], p=[0.999, 0.001]):
            self.position = list(nearest)
            self.decrement_food(distance(self.position, nearest) * self.__food_unit)
            self.check_for_death()
            if self.status == 'dead':
                return self
            if resource == 'food':
                self.food_level = 100
            elif resource == 'shelter':
                self.sheltered = True
            else:
                raise ValueError("Unknown resource sought")
            return self, distance(self.position, nearest)

        # Moves randomly instead of seeking resource. Better luck next time.
        else:
            self.random_move()
            self.food_level -= self.__food_unit
            return self, 1


def distance(x: list, y: tuple) -> int:
    return abs(x[0] - y[0]) + abs(x[1] - y[1])


def increment_day(hrs: int, secs: int) -> (int, int, int):
    '''
    This takes seconds and hours and increments it according to a 24-hour clock
    :param hrs: integer number of hours, from 0-23.
    :param secs: arbitrary number of integer seconds. For every 3600 seconds, it will add an hour.
    :return: returns the new value for hours and seconds
    >>> increment_day(5, 87273)
    1, 4, 873
    '''
    days = 0
    while secs >= 3600:
        hrs += 1
        secs -=3600  # reduce seconds by 3600 and add an hour
        # at midnight the 24-clock cycles back around to 0
        if hrs == 24:
            hrs = 0
            days += 1
    return days, hrs, secs


def create_standard_test(iterations: int) -> CropField:
    # fields are assumed to have a scale 1 cell has dimension 15 meters x 15 meters
    # create the top row of the field
    base_field_base_rows = [2] * 100
    base_field_base_rows[0] = 3
    base_field_base_rows[99] = 3
    # create the bottom row_len of the field
    base_field_bottom_rows = [3] * 100
    # create the standard middle row
    base_field_middle_rows = [1] * 100
    base_field_middle_rows[0] = 3
    base_field_middle_rows[99] = 3
    # Build up a single standard field
    standard_field = [base_field_base_rows]
    for j in range(98):
        standard_field.append(base_field_middle_rows)
    standard_field.append(base_field_bottom_rows)
    # create the standard test site
    construction = []
    for j in range(0, iterations + 1):
        construction += standard_field
    return CropField(construction)


def create_food_heavy_test(iterations: int) -> CropField:
    # fields are assumed to have a scale 1 cell has dimension 15 meters x 15 meters
    # create the top and bottom row_len of the field
    base_field_base_rows = [2] * 100
    # create the standard middle row
    base_field_middle_rows = [1] * 100
    base_field_middle_rows[0] = 2
    base_field_middle_rows[99] = 2
    base_bottom_row = [3] * 100
    # Build up a single standard field
    standard_field = [base_field_base_rows]
    for j in range(0, 98):
        standard_field.append(base_field_middle_rows)
    standard_field.append(base_bottom_row)
    # create the standard test site
    construction = []
    for j in range(0, iterations + 1):
        construction += standard_field
    return CropField(construction)


def create_shelter_heavy_test(iterations: int) -> CropField:
    # fields are assumed to have a scale 1 cell has dimension 15 meters x 15 meters
    # create the top and bottom row_len of the field
    base_field_base_rows = [3] * 100
    base_field_base_rows[0] = 3
    base_field_base_rows[99] = 3
    # create the standard middle row
    base_field_middle_rows = [1] * 100
    base_field_middle_rows[0] = 2
    base_field_middle_rows[99] = 2
    # Build up a single standard field
    standard_field = [base_field_base_rows]
    for j in range(0, 98):
        standard_field.append(base_field_middle_rows)
    standard_field.append(base_field_base_rows)
    # create the standard test site
    construction = []
    for j in range(0, iterations + 1):
        construction += standard_field
    return CropField(construction)


def create_middle_food_windbreak_test(iterations: int) -> CropField:
    # fields are assumed to have a scale 1 cell has dimension 15 meters x 15 meters
    # create the top and bottom row_len of the field
    base_field_base_rows = [3] * 100
    # create the standard middle row
    base_field_middle_rows = [1] * 100
    base_field_middle_rows[0] = 3
    base_field_middle_rows[99] = 3
    base_field_middle_rows[49] = 2
    # Build up a single standard field
    standard_field = [base_field_base_rows]
    for j in range(0, 98):
        standard_field.append(base_field_middle_rows)
    standard_field.append(base_field_base_rows)
    # create the standard test site
    construction = []
    for j in range(0, iterations + 1):
        construction += standard_field
    return CropField(construction)


def create_middle_shelter_windbreak_test(iterations: int) -> CropField:
    # fields are assumed to have a scale 1 cell has dimension 15 meters x 15 meters
    # create the top and bottom row_len of the field
    base_field_base_rows = [2] * 100
    # create the standard middle row
    base_field_middle_rows = [1] * 100
    base_field_middle_rows[0] = 2
    base_field_middle_rows[99] = 2
    base_field_middle_rows[49] = 3
    # Build up a single standard field
    standard_field = [base_field_base_rows]
    for j in range(0, 98):
        standard_field.append(base_field_middle_rows)
    standard_field.append(base_field_base_rows)
    # create the standard test site
    construction = []
    for j in range(0, iterations + 1):
        construction += standard_field
    return CropField(construction)


def create_test_food_test(iterations: int) -> CropField:
    # fields are assumed to have a scale 1 cell has dimension 15 meters x 15 meters
    # create the top and bottom row_len of the field
    base_field_base_rows = [2] * 100
    # Build up a single standard field
    standard_field = [base_field_base_rows]
    for j in range(0, 98):
        standard_field.append(base_field_base_rows)
    standard_field.append(base_field_base_rows)
    # create the standard test site
    construction = []
    for j in range(0, iterations + 1):
        construction += standard_field
    return CropField(construction)


def create_middle_shelter_windbreak_test_2(iterations: int) -> CropField:
    # fields are assumed to have a scale 1 cell has dimension 15 meters x 15 meters
    # create the top and bottom row_len of the field
    base_field_base_rows = [2] * 100
    # create the standard middle row
    base_field_middle_rows = [1] * 100
    base_field_middle_rows[0] = 2
    base_field_middle_rows[99] = 2
    base_field_middle_rows[49] = 3
    base_field_middle_rows_variant = [1] * 100
    base_field_middle_rows_variant[49] = 3
    # Build up a single standard field
    standard_field = [base_field_base_rows]
    for j in range(0, 24):
        standard_field.append(base_field_middle_rows_variant)
        standard_field.append(base_field_middle_rows_variant)
        standard_field.append(base_field_middle_rows)
        standard_field.append(base_field_middle_rows)
    standard_field.append(base_field_middle_rows_variant)
    standard_field.append(base_field_base_rows)
    # create the standard test site
    construction = []
    for j in range(0, iterations + 1):
        construction += standard_field
    return CropField(construction)


def test_field(dictionary, number):
    # This function takes care of some repetitive code I had written earlier. It's not perfect, but it works for now.
    start_time = time.time()
    if number == 0:
        field_to_test = create_standard_test(33)
    elif number == 1:
        field_to_test = create_food_heavy_test(33)
    elif number == 2:
        field_to_test = create_middle_food_windbreak_test(33)
    elif number == 3:
        field_to_test = create_middle_shelter_windbreak_test(33)
    elif number == 4:
        field_to_test = create_shelter_heavy_test(33)
    elif number == 5:
        field_to_test = CropField.random_field(3333, 100, 90, 5, 5)
    elif number == 6:
        field_to_test = CropField.random_field(3333, 100, 80, 15, 5)
    elif number == 7:
        field_to_test = CropField.random_field(3333, 100, 80, 5, 15)
    else:
        return dictionary
    results = []
    for j in range(1000):
        monarch1 = Monarch(field_to_test)
        monarch1.move_one_day()
        while monarch1.status == "alive":
            monarch1.move_one_day()
        results.append(monarch1.status)
    dictionary["test_field_{}".format(number)] = [100 * results.count('dead') / len(results)]
    print("Dead percentage = {:.2f}%".format(100 * results.count('dead') / len(results)))
    print("Exit percentage = {:.2f}%".format(100 * results.count('exit') / len(results)))
    print("--- %s seconds ---" % (time.time() - start_time))
    return dictionary


def iterate_field(field: CropField, type: str = None) -> CropField:
    food_index = np.where(field.array == 2)  # get locations of food in field
    shelter_indices = np.where(field.array == 3)  # get locations of shelter in field
    food_ix_ix = len(food_index[0])  # indices of the food indices
    shelter_ix_ix = len(shelter_indices[0])  # indices of the shelter indices
    max_len = len(field.array)
    max_width = len(field.array[0])
    iterated_field = field
    # This gets complicated, but I'm picking a random amount of food indices to randomly move
    if type is None or type == 'Both':
        food_sites_to_iterate = np.random.choice(food_ix_ix,
                                                 np.random.randint(food_ix_ix),
                                                 replace=False)  # choose a random number of food sites to move
        food_sites_to_iterate.sort()
        shelter_sites_to_iterate = np.random.choice(shelter_ix_ix,
                                                    np.random.randint(shelter_ix_ix),
                                                    replace=False)  # same but for shelter
        shelter_sites_to_iterate.sort()
    elif type == 'Death':
        food_sites_to_iterate = np.random.choice(food_ix_ix,
                                                 np.random.randint(food_ix_ix / np.random.randint(1, 11)),
                                                 replace=False)  # choose a random number of food sites to move
        food_sites_to_iterate.sort()
        shelter_sites_to_iterate = np.random.choice(shelter_ix_ix,
                                                    np.random.randint(shelter_ix_ix),
                                                    replace=False)  # same but for shelter
        shelter_sites_to_iterate.sort()
    else:
        food_sites_to_iterate = np.random.choice(food_ix_ix,
                                                 np.random.randint(food_ix_ix),
                                                 replace=False)  # choose a random number of food sites to move
        food_sites_to_iterate.sort()
        shelter_sites_to_iterate = np.random.choice(shelter_ix_ix,
                                                    np.random.randint(shelter_ix_ix / np.random.randint(1, 11)),
                                                    replace=False)  # same but for shelter
        shelter_sites_to_iterate.sort()
    for food in food_sites_to_iterate:
        # This if statement and the one below is my attempt to group together similar items. I feel
        # that is more realistic in a managed field. Certainly the results I was getting before
        # doing this were valid, but an equally distributed field of crops, food and shelter is probably
        # not viable at this time. Dropping these if statements will give fields with more uniform
        # distribution.
        try:
            if abs(food_index[0][food] - food_index[0][food+1]) <= 1 or \
                    abs(food_index[0][food] - food_index[0][food-1]) <= 1 or \
                    abs(food_index[1][food] - food_index[1][food+1]) <= 1 or \
                    abs(food_index[1][food] - food_index[1][food-1]) <= 1:
                pass
        except IndexError:
            pass
        else:
            random_x = np.random.randint(max(food_index[0][food] - np.random.randint(0.1*max_len), 0),
                                         min(food_index[0][food] + np.random.randint(0.1*max_len) + 1, max_len))
            random_y = np.random.randint(max(food_index[1][food] - np.random.randint(0.1*max_width), 0),
                                         min(food_index[1][food] + np.random.randint(0.1*max_width) + 1, max_width))
            iterated_field.array[food_index[0][food]][food_index[1][food]] = 1
            iterated_field.array[random_x][random_y] = 2
    for shelter in shelter_sites_to_iterate:
        try:
            if abs(shelter_indices[0][shelter] - shelter_indices[0][shelter+1]) <= 1 or \
                    abs(shelter_indices[0][shelter] - shelter_indices[0][shelter-1]) <= 1 or \
                    abs(shelter_indices[1][shelter] - shelter_indices[1][shelter+1]) <= 1 or \
                    abs(shelter_indices[1][shelter] - shelter_indices[1][shelter-1]) <= 1:
                pass
        except IndexError:
            pass
        else:
            random_x = np.random.randint(max(shelter_indices[0][shelter] - np.random.randint(0.1*max_len), 0),
                                         min(shelter_indices[0][shelter] + np.random.randint(0.1*max_len) + 1, max_len))
            random_y = np.random.randint(max(shelter_indices[1][shelter] - np.random.randint(0.1*max_width), 0),
                                         min(shelter_indices[1][shelter] + np.random.randint(0.1*max_width) + 1, max_width))
            iterated_field.array[shelter_indices[0][shelter]][shelter_indices[1][shelter]] = 1
            iterated_field.array[random_x][random_y] = 3
    return iterated_field


def parse_time(clocktime):
    hours = int(clocktime[0:2])
    minutes = int(clocktime[-3:-1])
    return (hours*60*60) + (minutes*60)


def optimize_field(field: CropField, dead_goal: int = 100, exit_goal: int = 0, num_iters: int = 25) -> CropField:
    # Simulate to see how well the field does
    test_flag = 1  # We'll count up a number of flags to see if we have found a stable configuration
    match_flag = False  # This will change once we find a candidate
    current_dead_result = dead_goal  # scores the current round of sims by how many died, trying to minimize
    current_exit_result = exit_goal  # scores the current round of sims by how many exited, trying to maximize
    optimization_parameter = ""  # the parameter we mananged to optimize
    counter = 0
    testing_fields = {}  # keep track of the fields tested
    current_field = field
    print("food: {}".format(field.get_food_amt()))
    print("shelter: {}".format(field.get_shelter_amt()))
    try:
        while test_flag < 6:
            results = []  # a list of results for the current round of simulations
            for k in range(100):
                test_butterfly = Monarch(current_field)
                test_butterfly.move_one_day()
                # this part keeps the simulation going until the b-fly dies or exits
                while test_butterfly.status == 'alive':
                    test_butterfly.move_one_day()
                results.append(test_butterfly.status)
            dead_percentage = results.count('dead')
            exit_percentage = results.count('exit')
            counter += 1
            # print some stats for the current test field, partly just to monitor progress
            print('Results for cycle {}'.format(counter))
            print("Dead percentage = {:.2f}%".format(dead_percentage))
            print("Exit percentage = {:.2f}%".format(exit_percentage))
            testing_fields[current_field] = dead_percentage, exit_percentage
            current_field = iterate_field(current_field, 'Both')
            if dead_percentage < current_dead_result and exit_percentage > current_exit_result:
                if ~test_flag:
                    print('Potential match.')
                test_flag = 0
                match_flag = True
                optimization_parameter = "Both"
                current_dead_result = dead_percentage
                current_exit_result = exit_percentage
            if match_flag:
                print("Testing potential match for {}".format(optimization_parameter))
                test_flag += 1
            else:
                current_field = iterate_field(current_field)
            if counter == num_iters:
                # After a few tries, we'll recalibrate by looking for whatever field had the lowest death count
                # and starting from there, to make sure we are moving in the right direction.
                # Just in case we started down a dead end series of iterations after a certain point.
                # The danger is that our fields will just get worse, so I added the keyboard interrupt option.
                print("Recalibrating....")
                best = min(testing_fields.items(), key=lambda x: x[1][0])
                testing_fields = {**testing_fields, **optimize_field(best[0], best[1][0], best[1][1])}
    except KeyboardInterrupt:
        print(current_field)
        pass

    print("food: {}".format(current_field.get_food_amt()))
    print("shelter: {}".format(current_field.get_shelter_amt()))
    print("Best field is field #{}, optimized for {}".format(counter - test_flag + 1, optimization_parameter))
    best = min(testing_fields.items(), key=lambda x: x[1][0])
    print("best: death - {}, exit - {}".format(best[1][0], best[1][1]))
    print(best[0])
    return testing_fields


def main():
    testfield = CropField.random_field(100,100,90,5,5)
    b1 = Monarch(testfield)
    print(b1.position)
    b1.simple_move('North')
    print(b1.position)

    # # this is the optimization simulation. Start with a random field and try to optimize it
    # testfield = CropField.random_field(3400, 100, 90, 5, 5)
    # print(testfield.row_len * 15, testfield.col_len * 15)
    # print('starting test')
    # clocktime = "00h01m"
    # clockseconds = parse_time(clocktime)
    # print(clockseconds)
    # p = optimize_field(testfield)



    # This is the basic simulation, run a bunch of single butterflies over the course of the day and see how they fare
    # testfield = create_test_food_test(33)
    # starttime = time.time()
    # results = []
    # for k in range(1000):
    #     monarch1 = Monarch(testfield)
    #     monarch1, seconds, hours = monarch1.move_one_day()
    #     results.append(monarch1.status)
    #
    # # basic results
    # print("Dead percentage = {:.2f}%".format(100 * results.count('dead') / len(results)))
    # print("Exit percentage = {:.2f}%".format(100 * results.count('exit') / len(results)))
    # print("--- %s seconds ---" % (time.time() - starttime))

    # first analysis
    # master_results = {}
    # for i in range(0, 8):
    #     test_field(master_results, i)
    # index = ['standard', 'food_heavy', 'middle_food', 'middle_shelter', 'shelter_heavy', 'balanced_random',
    #          'food_random', 'shelter_random']
    # master_results = pd.DataFrame(master_results).T
    # print(master_results)
    # master_results.index = index
    # print("The best-performing field was {}".format(master_results[0].idxmin()))


if __name__ == '__main__':
    main()

    # field stats
    # field = create_middle_shelter_windbreak_test(333)
    # food = len(field[field == 2].stack().index.tolist())
    # shelter = len(field[field == 3].stack().index.tolist())
    # crops = len(field[field == 1].stack().index.tolist())
    # total = food + shelter + crops
    # print('Percent food: {:.2f}%'.format(math.ceil(100 * food/total)))
    # print("Percent shelter: {:.2f}%".format(math.ceil(100 * shelter/total)))
    # print("Percent crops: {:.2f}%".format(math.floor(100 * crops/total)))

    # try to find an optimal random field
    # start_time = time.time()
    # score_dictionary = {}
    # for i in range(1000):
    #     field = CropField.random_field(3333, 100, 95, 4, 1)
    #     food_indices = create_food_table(field)
    #     shelter_indices = create_shelter_table(field)
    #     results = []
    #     for j in range(200):
    #         monarch1 = Butterfly(field)
    #         monarch1.move_one_day()
    #         results.append(monarch1.get_status())
    #     score_dictionary["test_field_{}".format(i)] = [(100 * (results.count('exit') / len(results))), field]
    #     print("--- %s seconds ---" % (time.time() - start_time))
    # df = pd.DataFrame(score_dictionary).T
    # print(df.loc[df[0].idxmax()][0])
    # print(df.loc[df[0].idxmax()][1])

    # Testing a higher crop percentage variant of the middle row_len
    # start_time = time.time()
    # field_test = create_middle_shelter_windbreak_test_2(333)
    # food_indices = create_food_table(field_test)
    # shelter_indices = create_shelter_table(field_test)
    # results = []
    # for j in range(100):
    #     monarch1 = Butterfly(field_test)
    #     monarch1.move_one_day()
    #     results.append(monarch1.get_status())
    # print("Dead percentage = {:.2f}%".format(100 * results.count('dead') / len(results)))
    # print("Exit percentage = {:.2f}%".format(100 * results.count('exit') / len(results)))
    # print("--- %s seconds ---" % (time.time() - start_time))
    #
    # food = len(field_test[field_test == 2].stack().index.tolist())
    # shelter = len(field_test[field_test == 3].stack().index.tolist())
    # crops = len(field_test[field_test == 1].stack().index.tolist())
    # total = food + shelter + crops
    # print('Percent food: {:.2f}%'.format(math.ceil(100 * food/total)))
    # print("Percent shelter: {:.2f}%".format(math.ceil(100 * shelter/total)))
    # print("Percent crops: {:.2f}%".format(math.floor(100 * crops/total)))
