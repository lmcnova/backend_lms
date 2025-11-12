# Department-Based Course Auto-Assignment

## Overview

This feature automatically assigns courses to students based on their department. When a student is created, they are automatically enrolled in all courses that match their department and have auto-assignment enabled.

## Key Features

✅ **Auto-assign on student creation** - Students automatically get enrolled in department courses
✅ **Auto-assign on course creation** - New courses automatically assign to existing students
✅ **Department filtering** - Students only see courses for their department
✅ **Flexible assignment** - Support for multiple departments per course
✅ **Manual override** - Admins/teachers can still manually assign courses

---

## How It Works

### 1. Course Configuration

When creating or updating a course, you can specify:

- **`departments`** - List of department names (e.g., ["Computer Science", "IT"])
- **`auto_assign`** - Boolean flag to enable automatic assignment

### 2. Student Creation

When a student is created with a department:

1. System searches for all courses with matching department AND `auto_assign: true`
2. Automatically creates assignments for those courses
3. Assignment is marked as assigned by "system"

### 3. Course Creation with Auto-Assign

When a course is created with `auto_assign: true`:

1. System finds all existing students in the specified departments
2. Automatically assigns the course to those students
3. Prevents duplicate assignments

---

## API Changes

### Modified Models

#### Course Model (`models/course.py`)

**New Fields:**
```python
departments: List[str] = []  # List of departments
auto_assign: bool = False     # Enable auto-assignment
```

**Example:**
```json
{
  "title": "Python Programming",
  "category": "Programming",
  "level": "beginner",
  "instructor_uuid": "teacher-uuid",
  "departments": ["Computer Science", "Information Technology"],
  "auto_assign": true
}
```

### New Endpoints

#### 1. Get Student's Department Courses
```
GET /student/me/courses
```

**Authentication:** Required (Student only)

**Description:** Returns all courses available for the student's department, including assignment status.

**Response:**
```json
{
  "courses": [
    {
      "uuid_id": "course-uuid",
      "title": "Python Programming",
      "category": "Programming",
      "level": "beginner",
      "departments": ["Computer Science"],
      "auto_assign": true,
      "is_assigned": true
    }
  ],
  "total": 1
}
```

### Modified Endpoints

#### 1. List Courses - Added Department Filter
```
GET /courses/?department=Computer%20Science
```

**New Query Parameter:**
- `department` (optional) - Filter courses by department

**Example:**
```bash
GET /courses/?department=Computer%20Science&level=beginner
```

---

## Usage Examples

### Example 1: Create Course with Auto-Assignment

```bash
POST /courses/
Authorization: Bearer <admin-or-teacher-token>
Content-Type: application/json

{
  "title": "Data Structures and Algorithms",
  "category": "Computer Science",
  "level": "intermediate",
  "description": "Learn DSA fundamentals",
  "instructor_uuid": "teacher-uuid-123",
  "departments": ["Computer Science", "Software Engineering"],
  "auto_assign": true,
  "tags": ["algorithms", "data-structures"]
}
```

**Result:**
- Course is created
- All existing students in "Computer Science" and "Software Engineering" departments are automatically assigned
- New students joining these departments will be auto-assigned

---

### Example 2: Create Student (Gets Auto-Assigned)

```bash
POST /student/
Content-Type: application/json

{
  "student_name": "John Doe",
  "department": "Computer Science",
  "email_id": "john@example.com",
  "password": "student123",
  "admin_uuid_id": "admin-uuid-123",
  "sub_department": "AI & ML"
}
```

**Result:**
- Student is created
- Automatically assigned to all courses where:
  - `departments` contains "Computer Science"
  - `auto_assign` is `true`

---

### Example 3: Student Views Available Courses

```bash
# Student login
POST /auth/login
{
  "email_id": "john@example.com",
  "password": "student123"
}

# Get department courses
GET /student/me/courses
Authorization: Bearer <student-token>
```

**Response:**
```json
{
  "courses": [
    {
      "uuid_id": "course-1",
      "title": "Python Programming",
      "departments": ["Computer Science"],
      "is_assigned": true
    },
    {
      "uuid_id": "course-2",
      "title": "Web Development",
      "departments": ["Computer Science"],
      "is_assigned": false
    }
  ],
  "total": 2
}
```

---

### Example 4: Filter Courses by Department

```bash
GET /courses/?department=Computer%20Science
```

Returns all courses available for Computer Science department.

---

## Assignment Logic

### When Student is Created

```python
# Automatically triggered in routes/student.py
auto_assign_courses_to_student(
    student_uuid="new-student-uuid",
    department="Computer Science",
    sub_department="AI & ML"  # optional
)
```

**Process:**
1. Find courses where `departments` contains "Computer Science"
2. Filter courses where `auto_assign` is `true`
3. Check if already assigned (skip if exists and active)
4. If previously revoked, re-activate the assignment
5. Create new assignment with `assigned_by_role: "system"`

### When Course is Created

```python
# Automatically triggered in routes/courses.py
if course.auto_assign and course.departments:
    auto_assign_existing_students_to_course(
        course_uuid="new-course-uuid",
        departments=["Computer Science", "IT"]
    )
```

**Process:**
1. Find all students where `department` is in the course's `departments` list
2. Check if already assigned
3. Create assignments for all matching students

---

## Database Schema Changes

### Courses Collection

**New Fields:**
```javascript
{
  // ... existing fields ...
  "departments": ["Computer Science", "Information Technology"],
  "auto_assign": true
}
```

### User Courses Collection (Assignments)

**System Assignments:**
```javascript
{
  "uuid_id": "assignment-uuid",
  "student_uuid": "student-uuid",
  "course_uuid": "course-uuid",
  "assigned_by_role": "system",  // Can be "admin", "teacher", or "system"
  "assigned_by_uuid": "auto-assign",
  "assigned_at": "2025-11-05T10:30:00Z",
  "status": "active"
}
```

---

## Common Use Cases

### Use Case 1: Department-Specific Curriculum

**Scenario:** Computer Science students need different courses than Mechanical Engineering students.

**Solution:**
1. Create courses with specific departments
2. Enable `auto_assign: true`
3. Students automatically see only relevant courses

### Use Case 2: Cross-Department Courses

**Scenario:** "Communication Skills" course is for all departments.

**Solution:**
```json
{
  "title": "Communication Skills",
  "departments": ["Computer Science", "Mechanical", "Electrical", "Civil"],
  "auto_assign": true
}
```

### Use Case 3: Optional Courses

**Scenario:** Some courses are available but not mandatory.

**Solution:**
```json
{
  "title": "Advanced Machine Learning",
  "departments": ["Computer Science"],
  "auto_assign": false  // Students can see it but aren't auto-enrolled
}
```

---

## Migration Guide

### For Existing Courses

Existing courses without `departments` field will:
- Have `departments: []` (empty array)
- Have `auto_assign: false`
- Continue working normally
- Can be updated to add departments

**Update existing course:**
```bash
PUT /courses/{course_uuid}
{
  "departments": ["Computer Science"],
  "auto_assign": true
}
```

### For Existing Students

Existing students:
- Will not be auto-assigned to existing courses
- Will be auto-assigned to new courses created with `auto_assign: true`
- Can be manually assigned via the assignments endpoint

**Bulk assign existing students:**
Create a course with departments and `auto_assign: true`, and all existing students in those departments will be assigned.

---

## Testing

Run the test script to see the feature in action:

```bash
python test_department_assignment.py
```

This script demonstrates:
1. Creating a course with departments and auto-assign
2. Creating students in different departments
3. Verifying auto-assignment works correctly
4. Checking that students only see department-relevant courses

---

## Utility Functions

Located in `utils/auto_assign.py`:

### 1. `auto_assign_courses_to_student()`
Assigns courses to a student based on department.

### 2. `get_available_courses_for_student()`
Gets all courses for a student's department with assignment status.

### 3. `auto_assign_existing_students_to_course()`
Assigns a course to all existing students in matching departments.

---

## Best Practices

✅ **Use clear department names** - Use consistent naming (e.g., "Computer Science" not "CS" or "Comp Sci")

✅ **Enable auto-assign for core courses** - Mandatory courses should have `auto_assign: true`

✅ **Leave auto-assign off for electives** - Let students choose optional courses

✅ **Use multiple departments carefully** - Only add departments where the course is truly relevant

✅ **Review assignments** - Use `GET /assignments/` to monitor auto-assignments

❌ **Don't change department names** - Will break existing assignments

❌ **Don't enable auto-assign for all courses** - Students may get overwhelmed

---

## Troubleshooting

### Student not getting auto-assigned?

Check:
1. Course has correct department name in `departments` array
2. Course has `auto_assign: true`
3. Student's department matches exactly (case-sensitive)
4. Student was created after course, or course was created after student

### Student seeing wrong courses?

Check:
1. Student's department field is correct
2. Course departments array is correct
3. Use `GET /student/me/courses` to verify

### How to manually assign?

Use the existing assignments endpoint:
```bash
POST /assignments/
{
  "course_uuid": "course-uuid",
  "student_uuid": "student-uuid"
}
```

---

## Future Enhancements

Potential improvements:
- Sub-department based filtering
- Year/semester based auto-assignment
- Prerequisite course checking
- Auto-assignment scheduling (delayed enrollment)
- Department hierarchy support
- Bulk assignment management UI

---

## Support

For issues or questions:
1. Check API documentation: http://localhost:8000/docs
2. Review this guide
3. Run test script for examples
4. Check server logs for errors
