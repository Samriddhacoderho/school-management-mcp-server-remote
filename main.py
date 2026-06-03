from fastmcp import FastMCP
import firebase_admin
from firebase_admin import credentials, db
from uuid import uuid4
import os
import json
import sys

print(f"CWD = {os.getcwd()}", file=sys.stderr)
print(f"FILE = {__file__}", file=sys.stderr)

# -----------------------------
# Firebase Initialization
# -----------------------------

firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS")

if firebase_creds_json:
    # Production: Load credentials from environment variable
    cred_dict = json.loads(firebase_creds_json)
    cred = credentials.Certificate(cred_dict)
else:
    # Local Development: Load serviceAccountKey.json
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")

    print(
        f"Using Firebase credentials file: {SERVICE_ACCOUNT_PATH}",
        file=sys.stderr,
    )

    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)

firebase_admin.initialize_app(
    cred,
    {
        "databaseURL": "https://school-management-mcp-default-rtdb.firebaseio.com/"
    },
)

# -----------------------------
# MCP Server
# -----------------------------
mcp = FastMCP("SchoolManagementMCP")


# -----------------------------
# Add Student
# -----------------------------
@mcp.tool
def add_student(
    name: str,
    student_class: str,
    roll_no: str,
    contact_number: str,
    address: str,
):
    """
    Add a new student.
    """

    student_id = str(uuid4())

    student_data = {
        "name": name,
        "class": student_class,
        "roll_no": roll_no,
        "contact_number": contact_number,
        "address": address,
        "fee_paid": False,
    }

    db.reference(f"students/{student_id}").set(student_data)

    return {
        "success": True,
        "student_id": student_id,
        "message": "Student added successfully",
    }


# -----------------------------
# Get Student
# -----------------------------
@mcp.tool
def get_student(student_id: str):
    """
    Get student details.
    """

    student = db.reference(f"students/{student_id}").get()

    if not student:
        return {"success": False, "message": "Student not found"}

    return student


# -----------------------------
# Get All Students
# -----------------------------
@mcp.tool
def get_all_students():
    """
    Fetch all students.
    """

    students = db.reference("students").get()

    return students or {}


# -----------------------------
# Update Student
# -----------------------------
@mcp.tool
def update_student(
    student_id: str,
    name: str = None,
    student_class: str = None,
    roll_no: str = None,
    contact_number: str = None,
    address: str = None,
):
    """
    Update student information.
    """

    ref = db.reference(f"students/{student_id}")

    student = ref.get()

    if not student:
        return {"success": False, "message": "Student not found"}

    updates = {}

    if name:
        updates["name"] = name

    if student_class:
        updates["class"] = student_class

    if roll_no:
        updates["roll_no"] = roll_no

    if contact_number:
        updates["contact_number"] = contact_number

    if address:
        updates["address"] = address

    ref.update(updates)

    return {
        "success": True,
        "message": "Student updated successfully",
    }


# -----------------------------
# Mark Fee Paid
# -----------------------------
@mcp.tool
def update_fee_status(student_id: str, fee_paid: bool):
    """
    Update fee payment status.
    """

    ref = db.reference(f"students/{student_id}")

    student = ref.get()

    if not student:
        return {"success": False, "message": "Student not found"}

    ref.update({"fee_paid": fee_paid})

    return {
        "success": True,
        "message": "Fee status updated",
    }


# -----------------------------
# Get Contact Number
# -----------------------------
@mcp.tool
def get_contact_number(student_id: str):
    """
    Get student's contact number.
    """

    student = db.reference(f"students/{student_id}").get()

    if not student:
        return {"success": False, "message": "Student not found"}

    return {
        "student_name": student["name"],
        "contact_number": student["contact_number"],
    }


# -----------------------------
# Delete Student
# -----------------------------
@mcp.tool
def delete_student(student_id: str):
    """
    Delete a student.
    """

    ref = db.reference(f"students/{student_id}")

    student = ref.get()

    if not student:
        return {"success": False, "message": "Student not found"}

    ref.delete()

    return {
        "success": True,
        "message": "Student deleted successfully",
    }


# -----------------------------
# Search Student By Name
# -----------------------------
@mcp.tool
def search_student(name: str):
    """
    Search students by name.
    """

    students = db.reference("students").get()

    if not students:
        return []

    results = []

    for student_id, student in students.items():
        if name.lower() in student["name"].lower():
            results.append(
                {
                    "student_id": student_id,
                    **student,
                }
            )

    return results


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=9000)