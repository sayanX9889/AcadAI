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
        return;
    }

    try {

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

                        const profilePicture =
                            String(
                                profile.profile_picture
                            ).trim();


                        /*
                         * Cloudinary returns a complete
                         * HTTPS URL.
                         *
                         * Example:
                         * https://res.cloudinary.com/...
                         *
                         * Use Cloudinary URLs directly.
                         */

                        if (
                            profilePicture.startsWith("http://") ||
                            profilePicture.startsWith("https://")
                        ) {

                            image.src =
                                profilePicture;

                        }

                        /*
                         * Backward compatibility for
                         * old Render/local profile pictures.
                         */

                        else {

                            image.src =
                                API_URL +
                                (
                                    profilePicture.startsWith("/")
                                        ? profilePicture
                                        : "/" + profilePicture
                                );

                        }


                        /*
                         * If the image cannot be loaded,
                         * show the default avatar instead
                         * of a broken-image icon.
                         */

                        image.onerror =
                            function () {

                                this.onerror = null;

                                this.src =
                                    "https://ui-avatars.com/api/?name=Student&background=e0e7ff&color=4f46e5&size=128";

                            };

                    }

                    else {

                        image.src =
                            "https://ui-avatars.com/api/?name=Student&background=e0e7ff&color=4f46e5&size=128";

                    }

                }
            );


            // ------------------------------
            // Student name
            // ------------------------------

            const studentNameElements =
                document.querySelectorAll(
                    ".student-name"
                );


            studentNameElements.forEach(
                function (element) {

                    if (profile.name) {

                        element.textContent =
                            profile.name;

                    }

                }
            );


            // ------------------------------
            // Student ID
            // ------------------------------

            const studentIdElements =
                document.querySelectorAll(
                    ".student-id"
                );


            studentIdElements.forEach(
                function (element) {

                    if (profile.student_id) {

                        element.textContent =
                            profile.student_id;

                    }

                }
            );


            // ------------------------------
            // Email
            // ------------------------------

            const studentEmailElements =
                document.querySelectorAll(
                    ".student-email"
                );


            studentEmailElements.forEach(
                function (element) {

                    if (profile.email) {

                        element.textContent =
                            profile.email;

                    }

                }
            );


            // ------------------------------
            // Department
            // ------------------------------

            const studentDepartmentElements =
                document.querySelectorAll(
                    ".student-department"
                );


            studentDepartmentElements.forEach(
                function (element) {

                    if (profile.department) {

                        element.textContent =
                            profile.department;

                    }

                }
            );


            // ------------------------------
            // Year
            // ------------------------------

            const studentYearElements =
                document.querySelectorAll(
                    ".student-year"
                );


            studentYearElements.forEach(
                function (element) {

                    if (profile.year) {

                        element.textContent =
                            profile.year;

                    }

                }
            );

        }

    }

    catch (error) {

        console.error(
            "Unable to load student profile:",
            error
        );

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
        "student_profile"
    );

    localStorage.removeItem(
        "token"
    );

    localStorage.removeItem(
        "access_token"
    );


    window.location.href =
        "login.html";

}


// ==========================================
// DELETE ACCOUNT
// ==========================================

async function deleteAccount() {

    if (!STUDENT_ID) {

        alert(
            "No logged-in student found."
        );

        return;

    }


    const confirmed =
        confirm(
            "Are you sure you want to permanently delete your account? This action cannot be undone."
        );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                `${API_URL}/auth/delete-account/${STUDENT_ID}`,
                {
                    method: "DELETE"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to delete account."
            );

        }


        localStorage.removeItem(
            "student_id"
        );

        localStorage.removeItem(
            "student_profile"
        );

        localStorage.removeItem(
            "token"
        );

        localStorage.removeItem(
            "access_token"
        );


        alert(
            "Your account has been deleted successfully."
        );


        window.location.href =
            "login.html";

    }

    catch (error) {

        console.error(
            "Account deletion error:",
            error
        );


        alert(
            error.message ||
            "Unable to delete account."
        );

    }

}


// ==========================================
// INITIALIZE AUTH
// ==========================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        loadStudentProfile();

    }
);