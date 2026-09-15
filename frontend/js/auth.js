// ==========================================
// AcadAI Advisor - Shared Authentication
// ==========================================

const API_URL = "https://acad-ai-backend-6494.onrender.com";


// ==========================================
// GET LOGGED-IN STUDENT
// ==========================================

const STUDENT_ID =
    localStorage.getItem("student_id");


// ==========================================
// REQUIRE LOGIN
// ==========================================

function requireLogin() {

    if (!STUDENT_ID) {

        window.location.href =
            "login.html";

        return false;
    }

    return true;
}


// ==========================================
// DEFAULT PROFILE ICON
// ==========================================

function setDefaultProfilePicture() {

    const profileImages =
        document.querySelectorAll(
            ".student-profile-image"
        );

    profileImages.forEach(function (image) {

        image.src =
            "https://ui-avatars.com/api/?name=Student&background=e0e7ff&color=4f46e5&size=128";

    });
}


// ==========================================
// LOAD STUDENT PROFILE
// ==========================================

async function loadStudentProfile() {

    if (!STUDENT_ID) {
        return null;
    }

    try {

        // ----------------------------------
        // Load academic student information
        // ----------------------------------

        const studentResponse =
            await fetch(
                `${API_URL}/students/${STUDENT_ID}`
            );

        if (!studentResponse.ok) {

            throw new Error(
                `Student API returned ${studentResponse.status}`
            );
        }

        const student =
            await studentResponse.json();

        if (student.error) {

            throw new Error(
                student.error
            );
        }


        // ----------------------------------
        // Student name
        // ----------------------------------

        const nameElements =
            document.querySelectorAll(
                "#sidebar-student-name"
            );

        nameElements.forEach(function (element) {

            element.textContent =
                student.name || "Student";

        });


        // ----------------------------------
        // Student ID
        // ----------------------------------

        const idElements =
            document.querySelectorAll(
                "#sidebar-student-id"
            );

        idElements.forEach(function (element) {

            element.textContent =
                student.student_id ||
                STUDENT_ID;

        });


        // ----------------------------------
        // Semester
        // ----------------------------------

        const semesterElements =
            document.querySelectorAll(
                "#student-semester"
            );

        semesterElements.forEach(function (element) {

            if (
                student.current_semester !==
                undefined
            ) {

                element.textContent =
                    student.current_semester;
            }

        });


        // ----------------------------------
        // Footer semester
        // ----------------------------------

        const footerSemesterElements =
            document.querySelectorAll(
                "#footer-semester"
            );

        footerSemesterElements.forEach(
            function (element) {

                if (
                    student.current_semester !==
                    undefined
                ) {

                    element.textContent =
                        student.current_semester;
                }

            }
        );


        // ----------------------------------
        // Load account/profile information
        // ----------------------------------

        const profileResponse =
            await fetch(
                `${API_URL}/auth/profile/${STUDENT_ID}`
            );


        if (profileResponse.ok) {

            const profile =
                await profileResponse.json();


            // ------------------------------
            // Profile picture
            // ------------------------------

            const profileImages =
                document.querySelectorAll(
                    ".student-profile-image"
                );

            profileImages.forEach(
                function (image) {

                    if (
                        profile.profile_picture
                    ) {

                        image.src =
                            API_URL +
                            profile.profile_picture;

                    }

                    else {

                        image.src =
                            "https://ui-avatars.com/api/?name=Student&background=e0e7ff&color=4f46e5&size=128";

                    }

                }
            );


            // ------------------------------
            // Account name
            // ------------------------------

            const accountNameElements =
                document.querySelectorAll(
                    "#sidebar-student-name"
                );

            accountNameElements.forEach(
                function (element) {

                    if (profile.full_name) {

                        element.textContent =
                            profile.full_name;

                    }

                }
            );

        }


        return student;

    }

    catch (error) {

        console.error(
            "Student profile loading error:",
            error
        );

        // Don't leave broken images
        setDefaultProfilePicture();

        return null;
    }
}


// ==========================================
// LOGOUT
// ==========================================

function logout() {

    localStorage.removeItem(
        "student_id"
    );

    localStorage.removeItem(
        "student_name"
    );

    localStorage.removeItem(
        "student_email"
    );

    window.location.href =
        "login.html";
}


// ==========================================
// DELETE ACCOUNT
// ==========================================

async function deleteAccount() {

    const studentId =
        localStorage.getItem(
            "student_id"
        );

    if (!studentId) {

        alert(
            "No logged-in account was found."
        );

        return;
    }


    // ----------------------------------
    // CONFIRMATION
    // ----------------------------------

    const confirmation =
        confirm(
            "Are you sure you want to permanently delete your account?\n\n" +
            "This will delete your login account, academic profile, subjects, " +
            "semester data, and profile picture.\n\n" +
            "This action cannot be undone."
        );


    if (!confirmation) {

        return;
    }


    try {

        console.log(
            "Deleting account:",
            studentId
        );


        // ----------------------------------
        // DELETE ACCOUNT API
        // ----------------------------------

        const response =
            await fetch(
                `${API_URL}/auth/account/${encodeURIComponent(studentId)}`,
                {
                    method: "DELETE",

                    headers: {
                        "Accept":
                            "application/json"
                    }
                }
            );


        console.log(
            "Delete response status:",
            response.status
        );


        // ----------------------------------
        // READ RESPONSE
        // ----------------------------------

        const data =
            await response.json();


        console.log(
            "Delete response:",
            data
        );


        // ----------------------------------
        // SERVER ERROR
        // ----------------------------------

        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.error ||
                `Server returned ${response.status}`
            );
        }


        // ----------------------------------
        // DELETE FAILED
        // ----------------------------------

        if (!data.success) {

            throw new Error(
                data.message ||
                "Account deletion failed."
            );
        }


        // ----------------------------------
        // CLEAR LOGIN INFORMATION
        // ----------------------------------

        localStorage.removeItem(
            "student_id"
        );

        localStorage.removeItem(
            "student_name"
        );

        localStorage.removeItem(
            "student_email"
        );


        // ----------------------------------
        // CLEAR SESSION STORAGE
        // ----------------------------------

        sessionStorage.clear();


        // ----------------------------------
        // SUCCESS MESSAGE
        // ----------------------------------

        alert(
            "Your account has been deleted successfully."
        );


        // ----------------------------------
        // RETURN TO LOGIN
        // ----------------------------------

        window.location.replace(
            "login.html"
        );

    }

    catch (error) {

        console.error(
            "ACCOUNT DELETE ERROR:",
            error
        );


        alert(
            "Unable to delete your account.\n\n" +
            error.message
        );
    }
}


// ==========================================
// MAKE FUNCTIONS AVAILABLE TO HTML
// ==========================================
//
// Required because dashboard.html uses:
//
// onclick="deleteAccount()"
// onclick="logout()"
//
// ==========================================

window.deleteAccount =
    deleteAccount;

window.logout =
    logout;


// ==========================================
// PAGE INITIALIZATION
// ==========================================

document.addEventListener(
    "DOMContentLoaded",
    async function () {


        // ----------------------------------
        // CURRENT PAGE
        // ----------------------------------

        const currentPage =
            window.location.pathname
                .split("/")
                .pop();


        // ----------------------------------
        // LOGIN/SIGNUP PAGES
        // DO NOT REQUIRE AUTHENTICATION
        // ----------------------------------

        if (
            currentPage === "login.html" ||
            currentPage === "signup.html" ||
            currentPage === ""
        ) {

            return;
        }


        // ----------------------------------
        // PROTECT OTHER PAGES
        // ----------------------------------

        if (!requireLogin()) {

            return;
        }


        // ----------------------------------
        // LOAD PROFILE
        // ----------------------------------

        await loadStudentProfile();

    }
);