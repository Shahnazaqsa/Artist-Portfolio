from flask import (
    Flask,
    render_template,
    flash,
    request,
    send_from_directory,
    redirect,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, PasswordField
from wtforms.validators import DataRequired
from flask_mail import Mail
import os
import uuid
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    login_user,
    LoginManager,
    current_user,
    UserMixin,
    login_required,
    logout_user,
)


app = Flask(__name__)
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT="465",
    MAIL_USE_SSL=True,
    MAIL_USERNAME="darakshan312@gmail.com",
    MAIL_PASSWORD="gove cfnw moby ukes",
)
mail = Mail(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root@localhost/myart"
db = SQLAlchemy(app)

app.config["SECRET_KEY"] = "somethingnumberwebsite123456"
csrf = CSRFProtect(app)

# Single User Configuration
USERNAME = "admin"
password = "darakhshan@ambrani"
PASSWORD_HASH = generate_password_hash(password)
UPLOAD_FOLDER = "static/photos"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# User model for authentication
class User(UserMixin):
    def __init__(self, username):
        self.id = username


# User loader function
@login_manager.user_loader
def load_user(user_id):
    if user_id == USERNAME:
        return User(user_id)
    return None


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class Contact(db.Model):
    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    name = db.Column(db.String(), unique=False, nullable=False)
    email = db.Column(db.String(), unique=False, nullable=False)
    message = db.Column(db.String(), unique=False, nullable=False)


class ContactForm(FlaskForm):
    name = StringField("Enter Name", validators=[DataRequired()])
    email = StringField("Enter Email", validators=[DataRequired()])
    message = StringField("Message me", validators=[DataRequired()])
    submit = SubmitField()


class ProjectForm(FlaskForm):
    project_pic = FileField("Enter photo of your project", validators=[DataRequired()])
    submit = SubmitField()


class CalForm(FlaskForm):
    cal_pic = FileField("Enter photo of your project", validators=[DataRequired()])
    submit = SubmitField()


class Projects(db.Model):
    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    project_pic = db.Column(db.String(), unique=False, nullable=False)


class CalPro(db.Model):
    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    cal_pic = db.Column(db.String(), unique=False, nullable=False)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        if username == USERNAME and check_password_hash(PASSWORD_HASH, password):
            user = User(username)
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html", form=form)


@app.route("/", methods=["GET", "POST"])
def home():
    form = ContactForm()
    if form.validate_on_submit():
        entry = Contact(
            name=form.name.data, message=form.message.data, email=form.email.data
        )

        db.session.add(entry)
        db.session.commit()
        mail.send_message(
            "New Message From " + form.name.data,
            sender=form.email.data,
            recipients=["darakshan312@gmail.com"],
            body=form.message.data,
        )
        flash("Your message has been sent successfully!", "success")
        form.name.data = ""
        form.email.data = ""
        form.message.data = ""
        return render_template(
            "index.html", fragment="#contact", success=True, form=form
        )
    return render_template("index.html", fragment="#contact", form=form)


@app.route("/project", methods=["GET", "POST"])
def project():
    project_form = ProjectForm()
    cal_form = CalForm()

    if project_form.validate_on_submit():
        if "project_pic" in request.files:
            pic = request.files["project_pic"]
            if pic.filename != "":
                unique_id = str(uuid.uuid4())
                filename = secure_filename(pic.filename)
                p_pic = unique_id + "_" + filename
                pic_path = os.path.join(app.config["UPLOAD_FOLDER"], p_pic)
                pic.save(pic_path)
                entry = Projects(project_pic=p_pic)
                db.session.add(entry)
                db.session.commit()
                flash("Your project photo has been successfully added", "success")
                return redirect(url_for("project_view_custom"))

    if cal_form.validate_on_submit():
        if "cal_pic" in request.files:
            pic = request.files["cal_pic"]
            if pic.filename != "":
                unique_id = str(uuid.uuid4())
                filename = secure_filename(pic.filename)
                p_pic = unique_id + "_" + filename
                pic_path = os.path.join(app.config["UPLOAD_FOLDER"], p_pic)
                pic.save(pic_path)
                entry = CalPro(cal_pic=p_pic)
                db.session.add(entry)
                db.session.commit()
                flash("Your calligraphy photo has been successfully added", "success")
                return redirect(url_for("project_view_cal"))

    return render_template("project.html", project_form=project_form, cal_form=cal_form)


@app.route("/display_image/<filename>")
def display_image(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/delete_post/<int:id>")
@login_required
def delete_post(id):
    project = Projects.query.filter_by(id=id).first_or_404()
    if current_user.id == USERNAME:
        db.session.delete(project)
        db.session.commit()
        flash("Post removed successfully", "success")
    else:
        flash("You can only edit your post", "danger")

    return redirect(url_for("project_view"))


@app.route("/project_view_custom")
def project_view():
    projects = Projects.query.all()
    project_form = ProjectForm()
    return render_template(
        "project_view_custom.html", projects=projects, project_form=project_form
    )


@app.route("/project_view_cal")
def project_view_cal():
    cal_projects = CalPro.query.all()
    cal_form = CalForm()
    return render_template(
        "project_view_cal.html", cal_projects=cal_projects, cal_form=cal_form
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout Successfully ", "success")
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, port=5001)
