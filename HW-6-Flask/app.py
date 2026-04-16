from flask import Flask, render_template

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
    name = "Dear Student"
    return render_template("index.html", user_name=name, courses=courses)

@app.route('/courses')
def courses():
    return render_template("courses.html", courses=courses_list)

@app.route('/contact')
def contact():
    pass



if __name__ == '__main__':
    app.run(debug=True)