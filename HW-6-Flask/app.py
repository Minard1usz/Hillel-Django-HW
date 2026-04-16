from flask import Flask, render_template, request

app = Flask(__name__)

# courses_list = ['English', 'Spanish', 'French', 'German', 'Italian', 'Polish', 'Arabic', 'Chinese', 'Korean']
courses_list = [{'name': 'English', 'flag': 'gb'},
                {'name': 'Spanish', 'flag': 'es'},
                {'name': 'French', 'flag': 'fr'},
                {'name': 'German', 'flag': 'de'},
                {'name': 'Italian', 'flag': 'it'},
                {'name': 'Polish', 'flag': 'pl'},
                {'name': 'Ukrainian', 'flag': 'ua'},
                {'name': 'Arabic', 'flag': 'sa'},
                {'name': 'Chinese', 'flag': 'cn'},
                {'name': 'Korean', 'flag': 'kr'},]

@app.route('/')
def index():
    name = "Student"
    return render_template("index.html", user_name=name)

@app.route('/courses')
def courses():
    return render_template("courses.html", courses=courses_list)

@app.route('/contact', methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        user_name = request.form.get("username")
        user_email = request.form.get("email")
        message = request.form.get("message")

        print(f"The message from {user_name} ({user_email}): {message}")
        return f"<h3>Thank you, {user_name}! Your message has been sent! We will contact you soon! </h3><a href='/'>Return to main page</a>"

    return render_template("contact.html")

@app.route('/about')
def about():
    return render_template("about.html")


if __name__ == '__main__':
    app.run(debug=True)