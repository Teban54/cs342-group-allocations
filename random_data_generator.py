import random

NUM_STUDENTS = 150
NUM_TOPICS = 9
TOPIC_DISTR = [5, 30, 30, 20, 20, 10, 10, 8, 8]
FIND_GROUP_PROB = 0.5
IGNORE_PROB = 0.05

def rand_string(len):
    s = ""
    for i in range(len):
        s += chr(ord('a') + random.randint(0, 25))
    return s

def rand_preference(len=3):
    pref = []
    for i in range(len):
        x = random.choices(list(range(NUM_TOPICS)), TOPIC_DISTR)[0]
        while x in pref:
            x = random.choices(list(range(NUM_TOPICS)), TOPIC_DISTR)[0]
        pref.append(x)
    return pref

netids = []
for i in range(NUM_STUDENTS):
    s = rand_string(random.randint(3, 5))
    while s in netids:
        s = rand_string(random.randint(3, 5))
    netids.append(s)

remain_ids = list(range(NUM_STUDENTS))
groups = []
prefs = []
while remain_ids:
    x = remain_ids[0]
    group = [x]
    r = random.random()
    if len(remain_ids) > 1 and r < FIND_GROUP_PROB:  # Form a group
        y = random.choice(remain_ids[1:])
        group.append(y)
    remain_ids = [i for i in remain_ids if i not in group]
    if r < 1 - IGNORE_PROB:
        groups.append(group)
        prefs.append(rand_preference())

with open('test_netids.txt', 'w') as f:
    f.write('\n'.join(netids))

with open('test_preferences.txt', 'w') as f:
    for i in range(len(groups)):
        items = [netids[id] for id in groups[i]] + [str(x) for x in prefs[i]]
        f.write(', '.join(items) + '\n')
