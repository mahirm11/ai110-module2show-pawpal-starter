# PawPal+ Project Reflection

## 1. System Design

**Core Actions**
1. **Add a task** The user creates a pet care task (walk, feeding, meds, enrichment), settings its duration, priority, and any preferred time windows

2. **Set daily constraints** The user inputs how much time they have available today and any scheduling preferences (e.g., meds before a certain time), which the scheduler must respect

3. **Generate today's plan** The system produces an ordered schedule from the task list and constraints, and explains its reasoning (why tasks were ordered/included/deferred as they were).

**a. Initial design**

- Briefly describe your initial UML design.

My initial UML design includes an **owner** which owns one or more **pets**, and these pets need the owner to perform **tasks** for the pets to be taken care of properly. These tasks are scheduled in the **scheduler** and is used by the owner. 

- What classes did you include, and what responsibilities did you assign to each?

The owner has a name, available time, and dictionary of preferences; they can add a pet under their name, add a task for a pet, and set a constraint. The pet has a name, species, and age (but no action). The task has a name, type, duration, priority level, preferred time window, and can either be recurring or not recurring; it has a method for checking whether the task conflicts with other tasks. The scheduler has a list of tasks, and dictionary of constraints; some actions it can perform are generating the schedule from the list of tasks, explaining the reasoning, sort the list of tasks by priority, and detect conflicts from the list.

**b. Design changes**

- Did your design change during implementation?

- If yes, describe at least one change and why you made it.

The original skeleton had the right classes, but a few UML relationships 
weren't actually wired up in code. For example, `Pet` had no way to hold 
its own tasks, so I added `tasks: list[Task] = field(default_factory=list)` 
to `Pet` to reflect the `Pet → Task` relationship from the diagram. I also 
changed `Scheduler` to take an `owner` reference instead of a separate 
`tasks` list, so it derives its task list by flattening `owner.pets[*].tasks` 
rather than keeping its own copy — this avoids the two lists getting out 
of sync before any scheduling logic even exists.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

My scheduler's conflict detection is reporting, not avoidance — it never 
attempts to prevent overlapping placements, only flags them after the fact 
via `Scheduler.detect_conflicts()`. Task placement always uses the start of 
`preferred_time_window`, so any two tasks with overlapping preferred windows 
will always collide and always be flagged, with no attempt to auto-resolve.

Preferred time windows can encode real constraints (medication timing, a 
fixed walk-before-work window) that the scheduler has no way to know are 
flexible. Auto-resolving a conflict by silently shifting one task risks 
violating a constraint the owner never stated was negotiable. Flagging the 
conflict and letting the human decide respects that ambiguity, and treats a 
scheduling collision as a normal state of a multi-pet household — not an 
error the program should try to silently fix or crash on.
---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

Debugging errors with UI.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

Use different chats and make UML diagram

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

