# Create new file: backend/constants.py

CGC_CSE_SUBJECTS = {
    "Semester 1": ["Mathematics-I", "Communication Skills-I", "Engineering Physics", "Logical Thinking"],
    "Semester 2": ["Basic Data Structures", "Mathematics-II", "Digital Electronics", "AI Applications Lab"],
    "Semester 3": ["Computer Organization & Architecture", "Advanced Data Structures & Algorithms", "Python Programming", "DBMS", "Probability & Statistics"],
    "Semester 4": ["Software Engineering", "Operating Systems", "Object Oriented Programming using JAVA", "Design and Analysis of Algorithms", "Aptitude-II", "Soft Skills-II"],
    "Semester 5": ["Theory of Computation", "Soft Computing", "Software Engineering", "Minor Project"],
    "Electives": ["Machine Learning", "Cloud Computing", "Cybersecurity", "Blockchain", "Internet of Things"]
}

# Flattens the list for the select-box
ALL_SUBJECTS = [sub for sem in CGC_CSE_SUBJECTS.values() for sub in sem]