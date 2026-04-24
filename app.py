from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql

app = Flask(__name__)
app.secret_key = "careerbridge_secret_key"


def get_db():
    return pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="MySQL80",
        database="career_portal_db",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )


def fetch_one(query, params=None):
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            result = cursor.fetchone()
        return result
    finally:
        connection.close()


def fetch_all(query, params=None):
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            result = cursor.fetchall()
        return result
    finally:
        connection.close()


# ─────────────────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("Index.html")


# ─────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "").strip()

        if not email or not password or not role:
            flash("Please fill in email, password, and role.", "error")
            return redirect(url_for("login"))

        connection = get_db()
        try:
            with connection.cursor() as cursor:
                if role == "student":
                    cursor.execute(
                        "SELECT * FROM students WHERE email=%s AND password=%s",
                        (email, password)
                    )
                    user = cursor.fetchone()

                    if not user:
                        flash("Invalid student email or password.", "error")
                        return redirect(url_for("login"))

                    session.clear()
                    session["user_id"] = user["student_id"]
                    session["role"] = "student"
                    session["user_name"] = user["full_name"]
                    session["university"] = user["university"]
                    session["department"] = user["department"]
                    session["semester"] = user["semester"]

                    return redirect(url_for("dashboard"))

                elif role == "recruiter":
                    cursor.execute(
                        "SELECT * FROM recruiters WHERE email=%s AND password=%s",
                        (email, password)
                    )
                    user = cursor.fetchone()

                    if not user:
                        flash("Invalid recruiter email or password.", "error")
                        return redirect(url_for("login"))

                    session.clear()
                    session["user_id"] = user["recruiter_id"]
                    session["role"] = "recruiter"
                    session["user_name"] = user["full_name"]
                    session["company_name"] = user["company_name"]

                    return redirect(url_for("recruiter"))

                else:
                    flash("Invalid role selected.", "error")
                    return redirect(url_for("login"))

        except Exception as e:
            print(f"Login Error: {e}")
            flash("A server error occurred during login.", "error")
            return redirect(url_for("login"))
        finally:
            connection.close()

    return render_template("Login.html")


# ─────────────────────────────────────────────────────────
# STUDENT REGISTRATION
# ─────────────────────────────────────────────────────────
@app.route("/register/student", methods=["POST"])
def register_student():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    university = request.form.get("university", "").strip()
    department = request.form.get("department", "").strip()
    semester = request.form.get("semester", "").strip()

    if not all([full_name, email, password, university, department, semester]):
        flash("All student registration fields are required.", "error")
        return redirect(url_for("login"))

    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT student_id FROM students WHERE email=%s", (email,))
            if cursor.fetchone():
                flash("This student email is already registered.", "error")
                return redirect(url_for("login"))

            cursor.execute("""
                INSERT INTO students (full_name, email, password, university, department, semester)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (full_name, email, password, university, department, semester))

        connection.commit()
        flash("Student account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    except Exception as e:
        connection.rollback()
        print(f"Student Register Error: {e}")
        flash("Student registration failed.", "error")
        return redirect(url_for("login"))
    finally:
        connection.close()


# ─────────────────────────────────────────────────────────
# RECRUITER REGISTRATION
# ─────────────────────────────────────────────────────────
@app.route("/register/recruiter", methods=["POST"])
def register_recruiter():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    company_name = request.form.get("company_name", "").strip()

    if not all([full_name, email, password, company_name]):
        flash("All recruiter registration fields are required.", "error")
        return redirect(url_for("login"))

    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT recruiter_id FROM recruiters WHERE email=%s", (email,))
            if cursor.fetchone():
                flash("This recruiter email is already registered.", "error")
                return redirect(url_for("login"))

            cursor.execute("""
                INSERT INTO recruiters (full_name, email, password, company_name)
                VALUES (%s, %s, %s, %s)
            """, (full_name, email, password, company_name))

        connection.commit()
        flash("Recruiter account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    except Exception as e:
        connection.rollback()
        print(f"Recruiter Register Error: {e}")
        flash("Recruiter registration failed.", "error")
        return redirect(url_for("login"))
    finally:
        connection.close()


# ─────────────────────────────────────────────────────────
# STUDENT DASHBOARD
# ─────────────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    if session.get("role") != "student":
        flash("Please log in as a student first.", "error")
        return redirect(url_for("login"))

    student = fetch_one(
        "SELECT * FROM students WHERE student_id=%s",
        (session["user_id"],)
    )

    return render_template(
        "Dashboard.html",
        user_name=session.get("user_name", "Student"),
        student=student
    )


# ─────────────────────────────────────────────────────────
# JOBS PAGE
# ─────────────────────────────────────────────────────────
@app.route("/jobs")
def jobs():
    all_jobs = fetch_all("SELECT * FROM jobs_new ORDER BY job_id DESC")

    applied_job_ids = set()
    if session.get("role") == "student":
        rows = fetch_all(
            "SELECT job_id FROM applications_new WHERE student_id=%s",
            (session["user_id"],)
        )
        applied_job_ids = {row["job_id"] for row in rows}

    return render_template(
        "Jobs.html",
        jobs=all_jobs,
        applied_job_ids=applied_job_ids
    )


# ─────────────────────────────────────────────────────────
# APPLY TO JOB
# ─────────────────────────────────────────────────────────
@app.route("/apply_job/<int:job_id>", methods=["POST"])
def apply_job(job_id):
    if session.get("role") != "student":
        flash("Please log in as a student to apply.", "error")
        return redirect(url_for("login"))

    student_id = session["user_id"]

    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT application_id FROM applications_new WHERE student_id=%s AND job_id=%s",
                (student_id, job_id)
            )
            existing = cursor.fetchone()

            if existing:
                flash("You already applied for this job.", "error")
                return redirect(url_for("jobs"))

            cursor.execute("""
                INSERT INTO applications_new (student_id, job_id, status)
                VALUES (%s, %s, %s)
            """, (student_id, job_id, "Applied"))

        connection.commit()
        flash("Application submitted successfully.", "success")
        return redirect(url_for("jobs"))

    except Exception as e:
        connection.rollback()
        print(f"Apply Job Error: {e}")
        flash("Job application failed.", "error")
        return redirect(url_for("jobs"))
    finally:
        connection.close()


# ─────────────────────────────────────────────────────────
# RECRUITER DASHBOARD
# ─────────────────────────────────────────────────────────
@app.route("/recruiter")
def recruiter():
    if session.get("role") != "recruiter":
        flash("Please log in as a recruiter first.", "error")
        return redirect(url_for("login"))

    company_name = session.get("company_name", "")

    company_jobs = fetch_all(
        "SELECT * FROM jobs_new WHERE company_name=%s ORDER BY job_id DESC",
        (company_name,)
    )

    return render_template(
        "Recruiter.html",
        jobs=company_jobs,
        user_name=session.get("user_name", "Recruiter"),
        company_name=company_name
    )


# ─────────────────────────────────────────────────────────
# POST JOB
# ─────────────────────────────────────────────────────────
@app.route("/post_job", methods=["POST"])
def post_job():
    if session.get("role") != "recruiter":
        flash("Please log in as a recruiter first.", "error")
        return redirect(url_for("login"))

    job_title = request.form.get("job_title", "").strip()
    location = request.form.get("location", "").strip()
    country = request.form.get("country", "").strip()
    job_type = request.form.get("job_type", "").strip()
    salary = request.form.get("salary", "").strip()
    description = request.form.get("description", "").strip()

    company_name = session.get("company_name", "").strip()

    if not all([job_title, company_name, location, country, job_type, salary, description]):
        flash("All job posting fields are required.", "error")
        return redirect(url_for("recruiter"))

    connection = get_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO jobs_new (job_title, company_name, location, country, job_type, salary, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (job_title, company_name, location, country, job_type, salary, description))

        connection.commit()
        flash("Job posted successfully.", "success")
        return redirect(url_for("recruiter"))

    except Exception as e:
        connection.rollback()
        print(f"Post Job Error: {e}")
        flash("Failed to post job.", "error")
        return redirect(url_for("recruiter"))
    finally:
        connection.close()


# ─────────────────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)