# Activity Clarification Questions Prompt Template

### Task
- Generate relevant clarification questions based on activity details (name, description, level, category, sub-category)
- Identify gaps in activity understanding and requirements
- Ensure questions help clarify expectations and requirements for activity implementation
- Validate activity parameters and gather missing context

### Input
Activity Details Structure:
```
{{
    "name": "Activity name/title",
    "description": "Activity description",
    "level": "Difficulty/grade level",
    "category_name": "Main category",
    "sub_category_name": "Sub-category"
}}
```

### Definition
Clarification questions should:
- Focus on understanding activity requirements and expectations
- Identify missing or ambiguous information
- Validate activity parameters
- Ensure alignment with educational objectives
- Gather necessary implementation details
- Consider student engagement and learning outcomes

### Deliverable
- A set of 3-5 targeted clarification questions
- Questions should:
  - Address specific aspects of the activity
  - Help gather missing implementation details
  - Validate activity parameters
  - Ensure clear understanding of expectations
  - Focus on educational outcomes

## Instructions

### Do's
1. Start with questions about the core purpose and learning objectives
2. Ask about specific implementation requirements
3. Inquire about assessment criteria and success metrics
4. Question about resource requirements and constraints
5. Ask about student engagement and participation expectations
6. Inquire about integration with existing curriculum
7. Question about technical requirements and dependencies

### Don'ts
1. Avoid questions that can be derived from the activity details
2. Don't make assumptions about implementation
3. Avoid leading questions about activity design
4. Don't ask questions that are too broad or vague
5. Avoid questions about basic activity parameters already provided
6. Don't ask questions that don't contribute to understanding requirements
7. Avoid questions about hypothetical scenarios

## Example Prompts

### Example 1: Science Experiment Activity
Input:
```
{{
    "name": "Chemical Reaction Lab",
    "description": "Students will conduct experiments to observe chemical reactions",
    "level": "Grade 10",
    "category_name": "Science",
    "sub_category_name": "Chemistry"
}}
```

Output:
```
1. What specific chemical reactions should be included in the lab, and what safety measures need to be implemented for each?

2. What are the expected learning outcomes for students, and how will their understanding be assessed?

3. What materials and equipment will be required, and are there any specific budget constraints to consider?

4. How should students document their observations and findings, and what format should their lab reports follow?

5. Are there any specific curriculum standards or learning objectives that this activity needs to align with?
```

### Example 2: Programming Activity
Input:
```
{{
    "name": "Python Game Development",
    "description": "Create a simple game using Python programming",
    "level": "Intermediate",
    "category_name": "Computer Science",
    "sub_category_name": "Programming"
}}
```

Output:
```
1. What specific programming concepts should be demonstrated in the game, and what is the expected complexity level?

2. What are the minimum requirements for the game, and what additional features would be considered for higher grades?

3. How should students handle game assets and resources, and are there any specific libraries or frameworks they should use?

4. What is the expected timeline for completion, and how should students document their development process?

5. How will the games be evaluated, and what criteria will be used to assess student understanding of programming concepts?
```

## Usage Guidelines

1. Analyze the provided activity details carefully
2. Identify potential gaps in information
3. Focus on questions that will help clarify:
   - Learning objectives
   - Implementation requirements
   - Assessment criteria
   - Resource needs
   - Technical specifications
   - Student expectations
4. Ensure questions are specific to the activity type and level
5. Consider the educational context and curriculum alignment

## Output Format

Each set of clarification questions should be presented as:

```
Activity Details:
- Name: [Activity Name]
- Description: [Activity Description]
- Level: [Activity Level]
- Category: [Category Name]
- Sub-category: [Sub-category Name]

Identified Areas Needing Clarification:
- [Area 1]
- [Area 2]
- [Area 3]

Clarification Questions:
1. [Question 1]
2. [Question 2]
3. [Question 3]
4. [Question 4]
5. [Question 5]
```

Remember to:
- Focus on questions that will help understand the activity requirements
- Consider the educational context and learning objectives
- Ensure questions are specific to the activity type and level
- Validate all necessary parameters for successful implementation
- Consider both student and teacher perspectives

<<<<<<< HEAD
# USER INPUT
Input:
```
{activity_dictionary}
```

# OUTPUT
Output:
```
```
=======

## USER INPUT 

{user_input}

## OUTPUT
>>>>>>> bc4b5af (added templates)
