# Algorithm for Group Allocation for CompSci 342

This is an implementation of a Dynamic Programming-based group allocation
algorithm for the Spring 2020 offering of Duke University's CompSci 342 
class taught by Owen Astrachan. The algorithm is designed and implemented 
by Charles Lyu.

## Problem Statement

The class has at most 150 students, and they will be organized into
groups of 3 to 5 people with a preference for 4. Each group is assigned
to one of the 6 topics.

Students can submit their three most preferred topics either individually
or in pairs. Each of their three choices can be either a topic, or
"non-specified" (which means they can be assigned to any topic; this 
can be disabled by changing the ``ENABLE_NON_SPECIFIED`` parameter). 
Some students may not have submitted their preferences, and thus they 
can be assigned to any topic.

Our task is to assign students into groups such that:

- **Each student always gets one of the three topics they have chosen (or any
topic if they have chosen "non-specified")**, with a preference for the
first and then the second choices;

- The number of people in each group is always between 3 and 5, with a
preference for 4;

- The allocation is done in an optimal and fair manner as much as 
possible;

- **If a student did not give a preference (i.e. exists in the list of
NetIDs but not in list of preferences), they might be put in any group 
and any topic as deemed fit.**

(Note: The number of topics can be changed easily as described below,
although that may affect the efficiency of the algorithm. The *allowed 
number of people per group*, and the *maximum number of students who can
submit their choices together* (2), should NOT be changed.)

## Algorithm

### Background and setup

We interpret this as an optimization problem. Define an *objective value
(interpreted as global welfare)* as follows:

- **Each student that gave their preferences contributes to the global
objective based on which choice they got.** The exact values of 
contribution can be adjusted with the ``PREF_VALUES`` parameter.
    - For example, if ``PREF_VALUES = [8, 4, 2]``, every student that
    gets their first choice contributes 8 to the objective, every student
    that gets their second choice contributes 4, etc.
    - By default, this value is per capita: that is, a pair of students
    that submitted their choices together will contribute twice to
    the global objective. For example, a pair who gets their first choice
    will contribute 16.
        - To change this such that a pair only counts once, set 
        ``IS_VALUE_PER_PERSON`` to ``False``.
        
- **Each group of 3 or 5 people will deduct a value of 3 from the global
objective.** This is to encourage groups of 4.

Our goal is to maximize this objective value across all groups.

### Dynamic Program

I attempted to design a dynamic program that maximizes the objective.
**Unfortunately, the algorithm is not able to obtain the global maximum
value due to edge cases, but it can return a value that is approximately 
optimal** (and is probably optimal on a scale of 150 students).

Let ``f[i, l1, l2, l3, l4, l5, l6]`` be the maximum objective value
obtained from assigning the first ``i`` "preference groups" (individuals 
or pairs) into project groups of 3-5, with ``l1`` leftover students 
being assigned to topic 1 but have not yet formed a complete group,
``l2`` leftover students for topic 2, etc (0<=li<=5). 
Then, if ``p`` is the number of people in this preference group (1<=p<=2)
and ``v[i, t]`` is the preference value that i gets from being assigned
to topic t:

````
f[i, l1, l2, l3, l4, l5, l6] = max{
    f[i-1, l1-p, l2, ..., l6],   # Add i to the leftover crowd for topic 1, forming a new group of 4 if applicable
    f[i-1, x, l2, ..., l6] + (-3 if x != 4 else 0)  IF l1 == p and 3 <= x <= 5   # Start a new group of topic 1 from i, force the l1 leftover students to form a group of 3~5
    ...,
    f[i-1, l1, l2, ..., l6-p],
    f[i-1, l1, l2, ..., x]
}
````

Where each ``li-x`` is its remainder when divided by 4 if necessary.
If a preference group specified all 3 choices, only those 3 dimensions
will be considered.

A severe limitation is that the algorithm is only able to form groups
with students that are adjacent to each other in the list of preferences
(although some special cases are in place to partly overcome the issue).
Ultimately, this is the cause for the algorithm's non-optimality. Also
because of this, the list of preferences is shuffled before the algorithm
executes.

### Implementation details

- **CAUTION: The algorithm can take very long to run.** Using random
data of 150 students and 6 topics, the code runs in **5 minutes** on
my computer.
    - In theory the DP should be efficient enough given the constraints;
    however, in practice it runs way too slow, likely due to issues
    with Python.
- **The list of preferences is shuffled every time the algorithm is 
run**. There are two reasons:
    - To ensure **fairness**: Since the algorithm has a high chance of
    grouping a student with whoever is just before or after, the
    reshuffling enforces randomness in the groupings.
    - To deal with the non-optimality limitations, as discussed above.  
- Because of the non-optimality, the code in ``main.py`` currently 
performs **2 independent runs** of the algorithm (reshuffling for
each run), and take the maximum of those two.
    - The number of trials can be changed with the ``NUM_TRIALS``
    parameter.
- For efficiency, instead of computing the value for each state of the
dynamic program in backward order (presented above), the code
actually implements the algorithm in forward order, first gathering
all valid entries for group i-1, and then generating all possible next
states for group i.
- Since the ``max`` function in the DP equation often involves
breaking ties, the order of computation is important. To ensure 
fairness across topics, at each i-1, all possible states are examined
and expanded in random order, and all topics are also examined in random
order.

## Running the Program

1. Create two text files. One stores the NetIDs of all students, in
the following format, one per line:

````
ola
jrnf
rcd
ksm
...
````

The other stores the preferences of students (individuals or pairs).
Each line first lists the NetIDs of all students, and then lists their
1st, 2nd and 3rd choices of topics (1-indexed), all comma separated:

````
ola, rcd, 1, 3, 5
ksm, 3, 4, 7
...
````

**Note:** If ``ENABLE_NON_SPECIFIED = True``, **the greatest number among
topic choices (e.g. 7 if there are 7 *options*) represents the option
of "non-specified"**. In the example above, ``ksm`` has a first choice 
of 3 and a second choice of 4, but is fine with any topic (1, 2, 5, 6) as 
the third choice. If ``ENABLE_NON_SPECIFIED = False``, then the greatest 
number represents an actual topic.

2. Open ``main.py``, and change the following parameters if necessary:

- ``NETID_FILENAME``: Name and path of the text file with NetIDs.
- ``PREFERENCE_FILENAME``: Name and path of the text file with 
preferences.
- ``OUTPUT_FILENAME``: Name and path of the text file where the output
is written to.
- ``NUM_OPTIONS``: Number of ***options*** that students can choose.
**This includes "non-specified"**.
    - For example, if there are 6 topics but students can opt for
    "non-specified", ``NUM_OPTIONS`` should be 7.
- ``PREF_VALUES``: Values that students get from receiving their first,
second and third choices, respectively.
    - Currently its value is ``[8, 4, 2]``, which favors the first 
    choice but does not really emphasize the difference between second
    and third choices.
    - For example, if both first and second choices are to be favored,
    consider ``[8, 6, 2]`` instead.
- ``IS_VALUE_PER_PERSON``: If ``True``, the value above is applied for
each student: that means a pair of students submitting their preference
together gets twice the value (e.g. 16 for first choice). If ``False``,
the value is only counted once per preference group, regardless of how
many people made the preferences together.
- ``ODD_SIZE_GROUP_PENALTY``: Penalty from the objective value for each
group of size 3 or 5. *This should be a negative value.*
    - Note that if this parameter is too negative, the algorithm might
    favor putting a student in its second or third choices, rather than
    squeezing them in a group of 5 (vice versa for groups of 3).
- ``ENABLE_NON_SPECIFIED``: Whether the last option is interpreted as
"non-specified", as discussed above.
- ``NUM_TRIALS``: Number of independent trials (reshuffles) performed.
    - If the algorithm runs too long, consider changing this to 1.
    
3. Run ``main.py``. Be patient.
 
4. After a few minutes, an output file will be created with the detailed
group allocations, containing all group members' NetIDs and then the
topic:

````
ola, rcd, jrnf, ksm, 3
...
````

## Miscellaneous

The ``random_data_generator.py`` program generates random data based
on the parameter given. This file was written for testing and debugging.