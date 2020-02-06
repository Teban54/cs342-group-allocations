import random

NETID_FILENAME = 'test_netids.txt'
PREFERENCE_FILENAME = 'test_preferences.txt'
OUTPUT_FILENAME = 'test_output.txt'

# Parameters from problem statement
# Strongly recommended NOT to change these.
# Some parts of the algorithm rely specifically on these parameters (as well as the maximum preference group size of 2)
NUM_OPTIONS = 9  # This INCLUDES the "non-specified" option
GROUP_SIZE = 4
MIN_GROUP_SIZE = 3
MAX_GROUP_SIZE = 5

# Parameters introduced by the algorithm
# NOTE: Feel free to fine tune this based on needs and performance
PREF_VALUES = [8, 4, 2]  # Value gained by matching a person to its 1st, 2nd or 3rd choice, respectively (See README)
IS_VALUE_PER_PERSON = True  # Whether the preference value above is gained by each person (i.e. 2x for a group of two), or by each group
ODD_SIZE_GROUP_PENALTY = -3  # Penalty for each group whose size is not equal to GROUP_SIZE (typically negative)
ENABLE_NON_SPECIFIED = True  # Whether the LAST option represents "non-specified"
                             # If this is True, students who put "non-specified" as one of their preferences
                             # can be assigned to any topic, gaining the corresponding value.
NUM_TRIALS = 2  # Number of random trials executed


# ----------- DO NOT MODIFY anything below ----------- #
# (Unless you understand the algorithm well enough)

NUM_TOPICS = NUM_OPTIONS - (1 if ENABLE_NON_SPECIFIED else 0)  # Actual number of topics, does not include "non-specified"

# Instance variables
netids = []  # List of all NetIDs
netid_to_index = {}  # Dict mapping NetIDs to their index in netids list
groups = []  # List of lists of student indexes (students without preferences are added at the end)
prefs = []  # List of lists of topic indexes (students without preferences are listed as [-1])

f = []  # DP table (see README): each entry is a dict mapping a tuple of states (e.g. (0,1,0,2,0,2,1)) to value
alloc = []  # Decision table: each entry is a dict mapping a tuple of states to the decision made at this step
            # (i.e. Which topic was this person/group allocated to)
            # Each decision is represented as a 3-tuple (old_state, topic, mode),
            # mode=0 means add to existing group, mode=1 means new group

NEGATIVE_INFINITY = -1 * 10 ** 19


def read_netids(filename):
    """
    Reads list of NetIDs from input file.
    :param filename: Name of file
    """
    global netids
    global netid_to_index
    with open(filename, 'r') as f:
        lines = f.readlines()
        netids = [s.strip() for s in lines if s.strip() != '']
    netid_to_index = {netids[i]: i for i in range(len(netids))}


def read_prefs(filename):
    """
    Reads list of preferences from input file.
    Also adds students who did not submit their preference as individual gorups.
    (These students may be allocated to any topic or group)
    :param filename: Name of file
    """
    pref_submitted = set()
    with open(filename, 'r') as f:
        for line in f.readlines():
            if line.strip() == '':
                continue
            arr = line.split(',')
            arr = [s.strip() for s in arr]

            ppl = [netid_to_index[netid] for netid in arr[:-3]]
            groups.append(ppl)
            pref_submitted.update(ppl)

            pref = [(int(s)-1) for s in arr[-3:]]
            if ENABLE_NON_SPECIFIED:
                pref = [(x if x != NUM_TOPICS else -1) for x in pref]
            prefs.append(pref)
    # Adds students without preferences
    for i in range(len(netids)):
        if i not in pref_submitted:
            groups.append([i])
            prefs.append([-1])


def shuffle_groups():
    """
    Shuffle list of preferences in random order.
    """
    global groups, prefs
    tuples = [(groups[i], prefs[i]) for i in range(len(groups))]
    random.shuffle(tuples)
    groups = [x for (x, y) in tuples]
    prefs = [y for (x, y) in tuples]


def dp():
    """
    Computes the DP table. (See README for algorithm explanations)
    """
    # Helper functions
    def generate_states(old_state, topic, inc_amount=-1, fix_amount=-1):
        """
        Get a list of possible new states by increasing the number of leftover people of a certain topic from an old state.
        :param inc_amount: Number of people to be added to the leftover people from the old state
            (If they exceed GROUP_SIZE, those GROUP_SIZE people form a group, and the leftover ones remain in the new state)
        :param fix_amount: Number of people that are forced to start a new group;
            leftover people from old state forms their own group (if between MIN_GROUP_SIZE and MAX_GROUP_SIZE)
        :return: List of new states as tuple
        """
        new_amount = (fix_amount if fix_amount != -1 else old_state[topic] + inc_amount)
        new_amounts = []
        if new_amount <= MAX_GROUP_SIZE:
            new_amounts.append(new_amount)  # e.g. 5
        if new_amount > GROUP_SIZE:
            new_amounts.append(new_amount % GROUP_SIZE)  # e.g. 1
            # So that 5 people can either form a group on their own, or rearrange a group of 4 and have 1 person join the next group
        return [tuple((old_state[i] if i != topic else amount)
                      for i in range(len(old_state)))
                for amount in new_amounts]

    def calc_value(group, old_state, topic, inc_amount=-1, fix_amount=-1):
        """
        Calculate the objective value of a new state by transitioning from the given old state.
        Does not check whether there's a valid new amount (that's done by generate_states).
        :return: Value, or NEGATIVE_INFINITY if impossible
        """
        if inc_amount != -1 and fix_amount != -1:  # Shouldn't happen
            return NEGATIVE_INFINITY
        sum = f[group].get(old_state, NEGATIVE_INFINITY)
        if sum == NEGATIVE_INFINITY:
            return NEGATIVE_INFINITY

        # Value per capita gained from assigning current group
        assign_val = NEGATIVE_INFINITY
        if prefs[group] == [-1]:  # Group did not submit their preferences
            assign_val = 0
        else:
            if -1 in prefs[group]:  # Non-specified included as one of their preferences
                assign_val = PREF_VALUES[prefs[group].index(-1)]
            if topic in prefs[group]:
                assign_val = max(assign_val, PREF_VALUES[prefs[group].index(topic)])
        if assign_val == NEGATIVE_INFINITY:  # Forces the group to only be assigned to one of their chosen topics
            return NEGATIVE_INFINITY
        sum += assign_val * (len(groups[group]) if IS_VALUE_PER_PERSON else 1)

        # In the case of using fix_amount (forcing the current group to start a new project group),
        # verify the old leftover amount is between MIN_GROUP_SIZE and MAX_GROUP_SIZE,
        # and apply odd size penalty
        if fix_amount != -1:
            old_amount = old_state[topic]
            if MIN_GROUP_SIZE <= old_amount <= MAX_GROUP_SIZE:
                sum += ODD_SIZE_GROUP_PENALTY if old_amount != GROUP_SIZE else 0
            else:
                return NEGATIVE_INFINITY  # Does not allow force starting even if old_amount=0

        return sum

    def update_values(new_row, new_alloc_row, new_states, new_value, decision_token):
        """
        Provide a possible objective value for a new state. Checks if that's better than its current value,
        and update if it is.
        :param row: Row as dict from f
        """
        if new_value <= NEGATIVE_INFINITY + 100:
            return
        # Update each new state to possibly improve its objective value
        for new_state in new_states:
            if new_row.get(new_state, NEGATIVE_INFINITY) < new_value:
                new_row[new_state] = new_value
                new_alloc_row[new_state] = decision_token

    # Generate initial state
    f.append({})
    alloc.append({})
    empty_state = (0,) * NUM_TOPICS
    f[0][empty_state] = 0
    alloc[0][empty_state] = (-1, -1)

    # DP on each preference group (note that f is 1-indexed)
    # i.e. f[i] + group[i] -> f[i+1]
    for i in range(0, len(groups)):
        print("Allocating group %d of %d..." % (i+1, len(groups)))

        old_row = f[-1]
        f.append({})
        alloc.append({})
        new_row = f[-1]
        new_alloc_row = alloc[-1]

        # Generate possible topics for group i, and shuffle in random order
        topics = prefs[i] if -1 not in prefs[i] else list(range(NUM_TOPICS))  # All topics to consider
        topics = list(topics)  # Clone
        random.shuffle(topics)
        num_ppl = len(groups[i])  # Number of people in this group

        # Generate all states in old row, and shuffle in random order
        old_states = list(old_row.keys())
        random.shuffle(old_states)

        # Based on each (calculated) feasible state in old_row, expand to new feasible states in new_row
        for old_state in old_states:
            for topic in topics:
                # Approach 1: Add this group to leftover people on this topic from old state
                new_states = generate_states(old_state, topic, inc_amount=num_ppl)
                new_value = calc_value(i, old_state, topic, inc_amount=num_ppl)
                #if new_value > NEGATIVE_INFINITY:
                #    print(old_state, old_row[old_state], i, topic, new_value)
                decision_token = (old_state, topic, 0)  # For alloc table
                update_values(new_row, new_alloc_row, new_states, new_value, decision_token)

                # Approach 2: Make this group the start of a new project group, forcing all leftover people to form a complete group
                new_states = generate_states(old_state, topic, fix_amount=num_ppl)
                new_value = calc_value(i, old_state, topic, fix_amount=num_ppl)
                decision_token = (old_state, topic, 1)
                update_values(new_row, new_alloc_row, new_states, new_value, decision_token)


def find_maxima():
    """
    Find all final states in the DP table that gives the solution with the maximum objective value.
    :return: - List of final states (empty if no feasible solutions)
             - Final objective value
    """
    max_value = NEGATIVE_INFINITY
    max_states = []

    def calc_final_value(state):
        """
        Calculate the final objective value of a state, after possible odd size penalties for leftover groups.
        :param state: Final state
        :return: Final objective value, or NEGATIVE_INFINITY if state is invalid
        """
        if state not in f[-1]:
            return NEGATIVE_INFINITY
        val = f[-1][state]
        for i in range(NUM_TOPICS):
            if state[i] == 0 or state[i] == GROUP_SIZE:
                pass
            elif MIN_GROUP_SIZE <= state[i] <= MAX_GROUP_SIZE:
                val += ODD_SIZE_GROUP_PENALTY
            else:
                return NEGATIVE_INFINITY
        return val

    for state in f[-1].keys():
        val = calc_final_value(state)
        if val <= NEGATIVE_INFINITY:
            continue
        #print(state, val, f[-1][state])
        if val > max_value:
            max_value = val
            max_states = [state]
        elif val == max_value:
            max_states.append(state)

    return max_states, max_value


def traceback(state):
    """
    Given an entry of the DP table, reconstruct the allocation of project groups.
    :param group: Group index
    :param state: Current state
    :return: List of tuples containing each project group's members (using preference group IDs) and topic, as follows:
        [([29, 41, 59], 3), ([1, 35], 5), ([27, 3], 2), ...]
    """
    project_groups = []  # Final output
    leftovers = [[] for _ in range(NUM_TOPICS)]  # Each topic's leftover preference groups

    # [Special Case 1]
    # During DP, we intentially allow an old leftover of 3 to roll into 3->1 or 3->5.
    # This is because if that happens, among the 3 leftover people, 1 of them must be from a single-person preference group,
    # So we can swap it and the current group, forming a group of 4 (including current group),
    # and 1 leftover which is that single-person preference group.
    # The following variables deals with this.
    three_to_one_marker = [False] * NUM_TOPICS
    three_to_one_leftovers = [[] for _ in range(NUM_TOPICS)]

    # [Special Case 2]
    # Since we allow leftover to go up to 5, it's possible to go from 5->2 or 5->3 by inc.
    # The following variables deal with this.
    five_to_twothree_marker = [False] * NUM_TOPICS

    def form_group(topic, leftover_source=leftovers):
        if len(leftover_source[topic]) == 0:
            return
        project_groups.append((leftover_source[topic], topic))
        leftover_source[topic] = []

    for group in range(len(groups)-1, -1, -1):  # 0-indexed
        #old_row = f[group]
        #new_row = f[group+1]
        new_alloc_row = alloc[group+1]
        old_state, topic, approach = new_alloc_row[state]
        #print(group, state, old_state, topic, approach, f[group][old_state], f[group+1][state])

        # Push current group to appropriate leftover stack
        if three_to_one_marker[topic] and len(groups[group]) == 1:
            # [Special Case 1]: Single found, complete single+B stack (see below)
            three_to_one_leftovers[topic].append(group)
            form_group(topic, leftover_source=three_to_one_leftovers)
            three_to_one_marker[topic] = False
        else:
            leftovers[topic].append(group)  # NOTE: For repeated 3->1 (see below), this will make leftovers[topic] have a size of 6

        if approach == 0:
            if old_state[topic] == 0:
                form_group(topic)
            elif old_state[topic] == GROUP_SIZE:  # 4->x
                if state[topic] < old_state[topic]:  # 4->1, 4->2: form new group
                    form_group(topic)
                elif five_to_twothree_marker[topic]:  # 4->5, need to form group manually if current 5 came from an inc 5->2 or 5->3
                    form_group(topic)
                    five_to_twothree_marker[topic] = False
                    # Note that if 5->23 marker is not active (which means 5 is followed by forced new group), no need to form here

            elif old_state[topic] < GROUP_SIZE and (  # 3->x
                    0 < state[topic] < old_state[topic]  # 3->1
                    or state[topic] > GROUP_SIZE and five_to_twothree_marker[topic]):  # 3->5 (only if 5->23 marker is active, similar to above)
                # *** [Special Case 1] ***
                # Essentially: Assuming 0 -(A)(single)-> 3 -(curr)-> 1 -(B)-> 0, currently leftovers[topic] contains curr and B;
                # We push B into three_to_one_leftovers[topic], which has the single from A as well as all of B (group of 4),
                # and use leftovers[topic] for curr and the rest of A (another group of 4).
                # Later when a single is found, instead of pushing it to leftovers, add it to three_to_one_leftovers and form group immediately.

                # There's one single exception, the "special case of special case":
                # Repeated 3->1's or 3->5's (e.g. 1a->2a->2b->2c->2d->2e->1b).
                # In this case, when we get here with the new group being 2b, 3->1 marker is True,
                # three_to_one_leftovers[topic] = [1b, 2e], and leftovers[topic] = [2d, 2c, 2b].
                # If this happens, we make [2d, 2c] form a new group, and then leave 2b in leftovers[topic].
                # Then we leave the 3->1 marker True, and keep doing this until a single-person group is found.

                if three_to_one_marker[topic]:  # Repeated 3->1 or 3->5
                    del leftovers[topic][-1]  # Remove 2b from [2d, 2c, 2b]
                    form_group(topic)
                    leftovers[topic].append(group)  # Add back 2b
                else:  # "Regular" 3->1 or 3->5: Start of marker
                    three_to_one_marker[topic] = True
                    three_to_one_leftovers[topic] = leftovers[topic][:-1]  # Contains B
                    leftovers[topic] = [group]  # curr

                if state[topic] > GROUP_SIZE and five_to_twothree_marker[topic]:  # Clear 5->23 marker if applicable
                    five_to_twothree_marker[topic] = False

            # [Special Case 2]
            elif old_state[topic] > GROUP_SIZE and state[topic] < old_state[topic]:  # 5->2, 5->3
                five_to_twothree_marker[topic] = True

        else:  # approach==1
            form_group(topic)

        state = old_state

        #print(project_groups)
        #print(leftovers)

    # Sanity check: Form all leftovers as groups
    # Should not need this, but just in case
    for topic in range(NUM_TOPICS):
        form_group(topic)

    return project_groups


def output(project_groups, filename):
    """
    Prints the group allocations to an output file in a human-readable format.
    :param project_groups: List of tuples containing each project group's members (using preference group IDs) and topic, as follows:
        [([29, 41, 59], 3), ([1, 35], 5), ([27, 3], 2), ...]
    :param filename: Name of output file
    """
    #print(project_groups)
    with open(filename, 'w') as f:
        for proj_group in project_groups:
            person_ids = [person_id for group_id in proj_group[0] for person_id in groups[group_id]]
            strs = [netids[id] for id in person_ids] + [str(proj_group[1] + 1)]
            f.write(', '.join(strs) + '\n')


def run():
    """
    Perform one run of the algorithm.

    Since the DP is dependent on the shuffled order of groups and may not always give a globally optimal solution,
    several runs are needed to reshuffle the groups and (hopefully) find a reasonable maximum.
    :return: - Objective value from this run
             - Project group allocation from this run
    """
    global f
    global alloc
    f = []
    alloc = []

    shuffle_groups()
    dp()

    """for g in range(len(groups)+1):
        print(g)
        print(f[g])
        print(alloc[g])"""

    max_states, max_value = find_maxima()
    if not max_states:
        return NEGATIVE_INFINITY, []
    max_state = random.choice(max_states)
    project_groups = traceback(max_state)

    return max_value, project_groups


def main():
    read_netids(NETID_FILENAME)
    read_prefs(PREFERENCE_FILENAME)

    max_value = NEGATIVE_INFINITY
    project_groups = []
    current_groups, current_prefs = [], []
    global groups, prefs
    for i in range(NUM_TRIALS):
        print("[Trial %d / %d]" % (i+1, NUM_TRIALS))
        value, proj_group = run()
        #print(value)
        if value > max_value:
            max_value = value
            project_groups = proj_group
            current_groups = list(groups)  # Keep track of this since it gets reshuffled later
            current_prefs = list(prefs)
        print()

    if max_value <= NEGATIVE_INFINITY:
        print("ERROR: No valid group allocations found.")
        return

    print("Optimal group allocation has an objective score of %d." % max_value)
    groups = current_groups
    prefs = current_prefs
    output(project_groups, OUTPUT_FILENAME)
    print("Detailed group allocation written to %s." % OUTPUT_FILENAME)


if __name__ == '__main__':
    main()